"""Files namespace.

Uploads the documents a project will ingest. A file lives under a *scope*, an
ordered list of up to five labels that works like a folder path, and is
identified by its database, scope and name together. Uploading the same name
under the same scope again stores the next version of that file rather than a
new one, so re-running an upload never duplicates documents.
"""

import json
import mimetypes
import re
import uuid
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import ExitStack
from datetime import datetime
from os import PathLike
from pathlib import Path
from typing import Any, NamedTuple

from requests_toolbelt import MultipartEncoder

from arango_ai_sdk._naming import FileManagerPath
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import (
    BatchTooLargeError,
    EmptyBatchError,
    EmptyFileError,
    FileUploadFailedError,
    InvalidFileMetadataError,
    InvalidScopeError,
    ServiceError,
)
from arango_ai_sdk.models import BatchItemResult, BatchUploadResult, UploadedFile

__all__ = ["FileManager"]

# The platform stores the files of a request one after another and answers only
# once the last one is written, so an upload can legitimately take minutes to
# get its response. The connection's default timeout is sized for quick calls;
# uploads replace it with this. It bounds the wait for the answer, not the
# transfer itself. The platform's gateway gives up after fifteen minutes, so a
# caller raising this further than that gains nothing.
UPLOAD_TIMEOUT = 300.0

# Rules the platform applies to a scope. Checked here as well because the
# platform validates only after the whole body has arrived: a bad label would
# otherwise surface after transferring every byte.
SCOPE_MAX_LABELS = 5
SCOPE_LABEL_MAX_LENGTH = 128
SCOPE_TOTAL_MAX_LENGTH = 256
_SCOPE_LABEL = re.compile(r"^[A-Za-z0-9_-]+$")

# What one batch request may carry. Larger sets are split into several requests.
BATCH_MAX_FILES = 100
BATCH_MAX_BYTES = 2 * 1024**3

_FALLBACK_CONTENT_TYPE = "application/octet-stream"


class _Planned(NamedTuple):
    """A file that has been placed and measured, ready to be batched."""

    path: Path
    name: str
    scope: tuple[str, ...]
    size: int


class FileManager:
    """Upload files through the communication layer.

    Parameters
    ----------
    communication : Communication
        Shared transport. This namespace calls ``send_request`` and nothing else.
    db_name : str
        Database the files are stored in. Taken from the client, so no upload
        asks for it.
    """

    def __init__(self, communication: Communication, db_name: str) -> None:
        self._communication = communication
        self._db_name = db_name

    def upload(
        self,
        path: str | PathLike[str],
        *,
        scope: Sequence[str] = (),
        name: str | None = None,
        custom_metadata: Mapping[str, str] | None = None,
        timeout: float = UPLOAD_TIMEOUT,
    ) -> UploadedFile:
        """Upload one file and return the stored version.

        The file is streamed from disk, never read into memory as a whole.

        Parameters
        ----------
        path : str or os.PathLike
            File to upload.
        scope : Sequence[str], optional
            Ordered scope labels the file is placed under, for example
            ``["acme", "legal"]``. Empty places it at the database root.
        name : str, optional
            Name the file is stored under. Defaults to the file's own name.
        custom_metadata : Mapping[str, str], optional
            Flat string-to-string metadata kept with this version and returned
            on later reads. Replaced, not merged, by the next version.
        timeout : float, optional
            Seconds to wait for the platform's answer. Raise it for very large
            files.

        Returns
        -------
        UploadedFile
            The stored version.

        Raises
        ------
        FileNotFoundError, IsADirectoryError
            ``path`` does not exist, or is a folder.
        InvalidScopeError
            ``scope`` breaks the platform's rules. Normally raised before
            sending, since the SDK applies the platform's rules first.
        EmptyFileError
            The file has no content. Normally raised before sending.
        InvalidFileMetadataError
            The platform rejected ``custom_metadata``.
        FileUploadFailedError
            The platform could not store the file and reports having rolled the
            upload back.
        ServiceError
            Any other error answer from the platform.
        """
        path = _existing_file(Path(path))
        labels = _validated_scope(scope)
        if path.stat().st_size == 0:
            raise EmptyFileError(f"File {str(path)!r} is empty.", status_code=422)
        file_name = name or path.name

        def fields(handles: ExitStack) -> list[tuple[str, Any]]:
            handle = handles.enter_context(path.open("rb"))
            return [
                ("name", file_name),
                *_scope_fields(labels),
                *_metadata_fields(custom_metadata),
                ("file", (file_name, handle, _content_type(file_name))),
            ]

        body = self._post_multipart(FileManagerPath.rag_input(self._db_name), fields, timeout)
        return _uploaded_file(body)

    def upload_many(
        self,
        paths: Iterable[str | PathLike[str]],
        *,
        scope: Sequence[str] = (),
        custom_metadata: Mapping[str, str] | None = None,
        timeout: float = UPLOAD_TIMEOUT,
    ) -> BatchUploadResult:
        """Upload several files under one scope, each by its own name.

        Files are sent in requests of at most 100 files and 2 GiB, the
        platform's limits, and processed independently: a file the platform
        rejects is reported in the result and does not stop the others. A
        request the platform fails as a whole is reported the same way, through
        the results of its files, so what earlier requests stored stays visible
        and the remaining requests still go ahead. Only errors the caller has
        to fix are raised.

        Parameters
        ----------
        paths : Iterable[str or os.PathLike]
            Files to upload.
        scope : Sequence[str], optional
            Ordered scope labels every file is placed under.
        custom_metadata : Mapping[str, str], optional
            Metadata kept with every uploaded version.
        timeout : float, optional
            Seconds to wait for the platform's answer to each request.

        Returns
        -------
        BatchUploadResult
            One result per file, in the given order.

        Raises
        ------
        FileNotFoundError, IsADirectoryError
            A path does not exist, or is a folder.
        InvalidScopeError
            ``scope`` breaks the platform's rules. Normally raised before
            sending.
        EmptyBatchError
            ``paths`` is empty. Raised before sending.
        BatchTooLargeError
            One file alone exceeds what a request may carry. Raised before
            sending; upload that file with :meth:`upload`.
        InvalidFileMetadataError
            The platform rejected ``custom_metadata``.
        """
        labels = _validated_scope(scope)
        plan = [_planned(Path(path), labels) for path in paths]
        return self._upload_planned(plan, custom_metadata, timeout)

    def upload_folder(
        self,
        folder: str | PathLike[str],
        *,
        scope: Sequence[str] = (),
        preserve_paths: bool = False,
        custom_metadata: Mapping[str, str] | None = None,
        timeout: float = UPLOAD_TIMEOUT,
    ) -> BatchUploadResult:
        """Upload every file under a folder, recursively.

        Same batching and error handling as :meth:`upload_many`.

        Parameters
        ----------
        folder : str or os.PathLike
            Folder to walk.
        scope : Sequence[str], optional
            Ordered scope labels the folder's files are placed under.
        preserve_paths : bool, optional
            When ``True``, each subfolder becomes one more scope label below
            ``scope``, keeping the folder structure. When ``False``, the
            default, every file is stored directly under ``scope`` by its own
            name, so two files with the same name in different subfolders
            become versions of one file.
        custom_metadata : Mapping[str, str], optional
            Metadata kept with every uploaded version.
        timeout : float, optional
            Seconds to wait for the platform's answer to each request.

        Returns
        -------
        BatchUploadResult
            One result per file, in path order.

        Raises
        ------
        NotADirectoryError
            ``folder`` does not exist, or is not a folder.
        InvalidScopeError
            ``scope``, or a subfolder name with ``preserve_paths``, breaks the
            platform's rules. Normally raised before sending.
        EmptyBatchError
            The folder holds no files. Raised before sending.
        BatchTooLargeError
            One file alone exceeds what a request may carry. Raised before
            sending; upload that file with :meth:`upload`.
        InvalidFileMetadataError
            The platform rejected ``custom_metadata``.
        """
        folder = Path(folder)
        if not folder.is_dir():
            raise NotADirectoryError(f"{str(folder)!r} is not a folder.")
        labels = _validated_scope(scope)
        plan = []
        for path in sorted(child for child in folder.rglob("*") if child.is_file()):
            file_scope = labels
            if preserve_paths:
                file_scope = _validated_scope([*labels, *path.relative_to(folder).parts[:-1]])
            plan.append(_planned(path, file_scope))
        return self._upload_planned(plan, custom_metadata, timeout)

    def _upload_planned(
        self,
        plan: list[_Planned],
        custom_metadata: Mapping[str, str] | None,
        timeout: float,
    ) -> BatchUploadResult:
        """Send placed files in as many requests as the platform's limits need."""
        if not plan:
            raise EmptyBatchError("There are no files to upload.", status_code=400)
        # Split before sending anything, so a file no request can carry is
        # refused while nothing has been stored yet.
        batches = list(_batches(plan))
        results: list[BatchItemResult] = []
        ok_count = error_count = 0
        for batch in batches:
            try:
                body = self._post_batch(batch, custom_metadata, timeout)
            except (InvalidScopeError, InvalidFileMetadataError, BatchTooLargeError):
                # The caller has to change the call; every request would fail the same way.
                raise
            except ServiceError as exc:
                # The request failed as a whole. Reporting its files as failed,
                # rather than raising, keeps what earlier requests stored visible
                # and lets the remaining requests go ahead.
                results.extend(_failed_item(planned, str(exc)) for planned in batch)
                error_count += len(batch)
                continue
            results.extend(_batch_item(item) for item in body["results"])
            ok_count += body["ok_count"]
            error_count += body["error_count"]
        return BatchUploadResult(self._db_name, results, ok_count, error_count)

    def _post_batch(
        self,
        batch: list[_Planned],
        custom_metadata: Mapping[str, str] | None,
        timeout: float,
    ) -> Any:
        """Send one batch request and return its parsed body."""
        # The manifest states each file's name and scope explicitly, so the
        # platform stores exactly what was validated here rather than deriving
        # the placement from the multipart file names.
        manifest = json.dumps(
            [{"file": i, "name": f.name, "scope": list(f.scope)} for i, f in enumerate(batch)]
        )

        def fields(handles: ExitStack) -> list[tuple[str, Any]]:
            return [
                ("manifest", manifest),
                *_metadata_fields(custom_metadata),
                *(
                    (
                        "files",
                        (f.name, handles.enter_context(f.path.open("rb")), _content_type(f.name)),
                    )
                    for f in batch
                ),
            ]

        return self._post_multipart(FileManagerPath.rag_input_batch(self._db_name), fields, timeout)

    def _post_multipart(
        self,
        path: str,
        fields: Callable[[ExitStack], list[tuple[str, Any]]],
        timeout: float,
    ) -> Any:
        """Post a multipart body built by ``fields`` and translate error answers.

        ``fields`` opens the files it needs through the stack it is given. It is
        called once per attempt: a retried request has to reopen files that the
        previous attempt read to the end.
        """
        # One boundary for every attempt, so the header, sent once, matches
        # each body the factory builds.
        boundary = uuid.uuid4().hex
        with ExitStack() as handles:

            def body() -> MultipartEncoder:
                # Release the previous attempt's handles before opening new ones.
                handles.close()
                return MultipartEncoder(fields=fields(handles), boundary=boundary)

            try:
                return self._communication.send_request(
                    "post",
                    path,
                    data=body,
                    headers={"content-type": f"multipart/form-data; boundary={boundary}"},
                    timeout=timeout,
                )
            except ServiceError as exc:
                named = _named_error(exc, batch=path.endswith("/batch"))
                if named is None:
                    raise
                raise named from exc


def _validated_scope(scope: Sequence[str]) -> tuple[str, ...]:
    """Return ``scope`` as a tuple, or raise if the platform would reject it."""
    labels = tuple(scope)
    if len(labels) > SCOPE_MAX_LABELS:
        raise InvalidScopeError(
            f"A scope has at most {SCOPE_MAX_LABELS} labels, got {len(labels)}.",
            status_code=400,
        )
    if sum(len(label) for label in labels) > SCOPE_TOTAL_MAX_LENGTH:
        raise InvalidScopeError(
            f"Scope labels combined exceed {SCOPE_TOTAL_MAX_LENGTH} characters.",
            status_code=400,
        )
    for label in labels:
        if not (0 < len(label) <= SCOPE_LABEL_MAX_LENGTH and _SCOPE_LABEL.fullmatch(label)):
            raise InvalidScopeError(
                f"Scope label {label!r} must be 1 to {SCOPE_LABEL_MAX_LENGTH} characters of "
                "letters, digits, underscores and hyphens.",
                status_code=400,
            )
    return labels


def _existing_file(path: Path) -> Path:
    """Return ``path`` once it is known to be an existing file, or say what it is instead."""
    if path.is_dir():
        raise IsADirectoryError(f"{str(path)!r} is a folder; upload folders with upload_folder.")
    if not path.is_file():
        raise FileNotFoundError(f"{str(path)!r} does not exist.")
    return path


def _planned(path: Path, scope: tuple[str, ...]) -> _Planned:
    """Place ``path`` under ``scope`` by its own name and record its size."""
    path = _existing_file(path)
    return _Planned(path, path.name, scope, path.stat().st_size)


def _failed_item(planned: _Planned, detail: str) -> BatchItemResult:
    """Report a planned file as not stored, with the platform's reason."""
    return BatchItemResult(name=planned.name, scope=planned.scope, status="error", detail=detail)


def _batches(plan: list[_Planned]) -> Iterator[list[_Planned]]:
    """Split the plan into requests the platform accepts, keeping file order."""
    batch: list[_Planned] = []
    size = 0
    for item in plan:
        if item.size > BATCH_MAX_BYTES:
            raise BatchTooLargeError(
                f"File {str(item.path)!r} is larger than the {BATCH_MAX_BYTES} bytes one "
                "request may carry; upload it on its own.",
                status_code=413,
            )
        if batch and (len(batch) == BATCH_MAX_FILES or size + item.size > BATCH_MAX_BYTES):
            yield batch
            batch, size = [], 0
        batch.append(item)
        size += item.size
    if batch:
        yield batch


def _scope_fields(labels: tuple[str, ...]) -> list[tuple[str, str]]:
    """Return the repeated ``scope`` form fields for ``labels``."""
    return [("scope", label) for label in labels]


def _metadata_fields(custom_metadata: Mapping[str, str] | None) -> list[tuple[str, str]]:
    """Return the ``custom_metadata`` form field, or nothing when none was given."""
    if custom_metadata is None:
        return []
    return [("custom_metadata", json.dumps(dict(custom_metadata)))]


def _content_type(name: str) -> str:
    """Guess a MIME type from the file name; the platform does the same on its side."""
    return mimetypes.guess_type(name)[0] or _FALLBACK_CONTENT_TYPE


def _named_error(exc: ServiceError, *, batch: bool) -> ServiceError | None:
    """Map an upload error answer onto the condition behind it.

    Returns ``None`` when the answer is not one the namespace knows, so the
    caller re-raises the generic error unchanged.
    """
    message = str(exc)
    # The message starts with the request line, which contains the database
    # name. Classify on the platform's own detail only, so a database called
    # "telescope" cannot turn every error into a scope error.
    _, _, detail = message.partition(f"failed with {exc.status_code}: ")
    codes = {"status_code": exc.status_code, "error_code": exc.error_code}
    if exc.status_code == 400 and "scope" in detail:
        return InvalidScopeError(message, **codes)
    if exc.status_code == 400 and "custom_metadata" in detail:
        return InvalidFileMetadataError(message, **codes)
    if exc.status_code == 413 and batch:
        return BatchTooLargeError(message, **codes)
    if exc.status_code == 422 and "cannot be empty" in detail:
        return EmptyFileError(message, **codes)
    # Only the platform's own storage failures promise a rollback; a 500 from
    # somewhere in between says nothing about what was stored.
    if exc.status_code == 500 and ("rolled back" in detail or "internal error" in detail):
        return FileUploadFailedError(message, **codes)
    return None


def _uploaded_file(body: Mapping[str, Any]) -> UploadedFile:
    """Build an :class:`UploadedFile` from a single-upload response body."""
    return UploadedFile(
        id=body["id"],
        name=body["name"],
        database=body["database"],
        scope=tuple(body.get("scope") or ()),
        content_type=body["content_type"],
        size=body["size"],
        uploaded_at=datetime.fromisoformat(body["uploaded_at"]),
        version=body["version"],
        safe_to_delete=body.get("safe_to_delete", True),
        metadata_key=body["metadata_key"],
        custom_metadata=dict(body.get("custom_metadata") or {}),
    )


def _batch_item(item: Mapping[str, Any]) -> BatchItemResult:
    """Build a :class:`BatchItemResult` from one entry of a batch response."""
    uploaded_at = item.get("uploaded_at")
    return BatchItemResult(
        name=item["name"],
        scope=tuple(item.get("scope") or ()),
        status=item["status"],
        detail=item.get("detail"),
        id=item.get("id"),
        version=item.get("version"),
        content_type=item.get("content_type"),
        size=item.get("size"),
        uploaded_at=datetime.fromisoformat(uploaded_at) if uploaded_at else None,
        metadata_key=item.get("metadata_key"),
        custom_metadata=dict(item.get("custom_metadata") or {}),
    )
