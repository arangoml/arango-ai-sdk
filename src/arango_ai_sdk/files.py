"""Files namespace.

Uploads the documents a project will ingest. A file is stored under a *scope*,
an ordered list of up to five labels that works like a storage path, and is
identified by its database, scope and name together. Uploading the same name
under the same scope again stores the next version of that file, never a
duplicate, so re-running an upload never duplicates documents.

Every upload in this module follows the same four steps:

1. Check locally what the platform would reject anyway: the paths, the scope
   and the limits of one request. If a check fails, nothing is sent.
2. Build the multipart form fields, opening the files so they stream from disk
   instead of being read into memory.
3. Send the request through :class:`~arango_ai_sdk.communication.Communication`
   and translate an error answer into a named exception.
4. Load the platform's reply into the models of :mod:`arango_ai_sdk.models`,
   which are generated from the file service's own API description.
"""

import json
import mimetypes
import re
import uuid
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import ExitStack
from os import PathLike
from pathlib import Path
from typing import Any

from requests_toolbelt import MultipartEncoder

from arango_ai_sdk._naming import FileManagerPath
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import (
    EmptyFileError,
    FileBatchTooLargeError,
    FileUploadFailedError,
    InvalidFileMetadataError,
    InvalidFileScopeError,
    ServiceError,
)
from arango_ai_sdk.models import (
    RagInputBatchItemResult,
    RagInputBatchUploadResponse,
    RagInputUploadResponse,
)

__all__ = ["FileManager"]

# The platform stores the files of a request one after another and answers only
# once the last one is written, so an upload can legitimately take minutes to
# get its response. The connection's default timeout is sized for quick calls;
# uploads replace it with ``UPLOAD_TIMEOUT``. It bounds the wait for the answer,
# not the transfer itself. The platform's gateway gives up after fifteen
# minutes, so a caller raising this further than that gains nothing.
UPLOAD_TIMEOUT = 300.0

# Rules the platform applies to a scope. Checked here as well because the
# platform validates only after the whole body has arrived: a bad label would
# otherwise surface after transferring every byte.
SCOPE_MAX_LABELS = 5
SCOPE_LABEL_MAX_LENGTH = 128
SCOPE_TOTAL_MAX_LENGTH = 256
_SCOPE_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

# What one request to the batch endpoint may carry. Checked here for the same
# reason as the scope: the platform only counts and measures once it has
# received everything.
BATCH_MAX_FILES = 100
BATCH_MAX_BYTES = 2 * 1024**3

_FALLBACK_CONTENT_TYPE = "application/octet-stream"

# A path as callers give it, and a scope: an ordered list of labels.
type FilePath = str | PathLike[str]
type Scope = Sequence[str]

# The multipart form fields of one request, in the order they are sent. A text
# field is ``(name, value)``; a file field is ``(name, (filename, handle, type))``.
type FormFields = list[tuple[str, Any]]

# One file to send and the scope it goes to, after the local checks passed.
type ScopedFile = tuple[Path, tuple[str, ...]]


class FileManager:
    """Manage the files a project will ingest, through the communication layer.

    Uploading is what it offers today; the rest of file management follows
    in later releases.

    Parameters
    ----------
    communication : Communication
        Shared transport. This namespace calls ``send_request`` and nothing else.
    db_name : str
        Database the files are organised under. The files themselves live in
        the platform's storage backend; the database scopes their management
        and access. Taken from the client, so no upload asks for it.
    """

    def __init__(self, communication: Communication, db_name: str) -> None:
        self._communication = communication
        self._db_name = db_name
        # Every endpoint of this file manager instance is scoped to ``db_name``.
        self._path = f"{FileManagerPath.PREFIX}/{db_name}/{FileManagerPath.RAG_INPUT}"

    def upload_file(
        self,
        path: FilePath,
        *,
        scope: Scope = (),
        name: str | None = None,
        custom_metadata: Mapping[str, str] | None = None,
        timeout: float = UPLOAD_TIMEOUT,
    ) -> RagInputUploadResponse:
        """Upload one file and return the stored version.

        The file is streamed from disk, never read into memory as a whole.

        Parameters
        ----------
        path : str or os.PathLike
            File to upload.
        scope : Sequence[str], optional
            Ordered scope labels the file is placed under, for example
            ``["acme", "legal"]``. No scoping means the file is
            database-scoped.
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
        RagInputUploadResponse
            The stored version, as the platform described it.

        Raises
        ------
        FileNotFoundError, IsADirectoryError
            ``path`` does not exist, or is a folder.
        InvalidFileScopeError
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
        file_path = _require_file(Path(path))
        _check_scope(scope)
        if file_path.stat().st_size == 0:
            raise EmptyFileError(f"File {str(file_path)!r} is empty.", status_code=422)
        stored_name = name or file_path.name

        def build_upload_fields(open_files: ExitStack) -> FormFields:
            """Build the form fields again for each attempt.

            A multipart file stream is consumed when sent, so a retry has to
            reopen the file. See ``_send_multipart``.
            """
            handle = open_files.enter_context(file_path.open("rb"))
            fields: FormFields = [("name", stored_name)]
            for label in scope:
                fields.append(("scope", label))
            if custom_metadata is not None:
                fields.append(("custom_metadata", json.dumps(dict(custom_metadata))))
            fields.append(("file", (stored_name, handle, _guess_content_type(stored_name))))
            return fields

        body = self._send_multipart(self._path, build_upload_fields, timeout)
        return RagInputUploadResponse.model_validate(body)

    def upload_files(
        self,
        files: Iterable[FilePath] | Mapping[FilePath, Scope],
        *,
        scope: Scope = (),
        custom_metadata: Mapping[str, str] | None = None,
        timeout: float = UPLOAD_TIMEOUT,
    ) -> list[RagInputBatchItemResult]:
        """Upload several files in one request, each stored under its own name.

        Give the files either as a list of paths that all share ``scope``, or
        as a mapping from path to scope when they go to different places. The
        platform stores them one by one: a file it rejects is reported in its
        own result and does not stop the others.

        One request carries at most 100 files and 2 GiB in total. Larger sets
        are refused before anything is sent; split them across calls.

        Parameters
        ----------
        files : Iterable[str or os.PathLike] or Mapping[str or os.PathLike, Sequence[str]]
            The files to upload: paths that all share ``scope``, or a mapping
            from each path to the scope it is placed under. A path listed
            twice is uploaded twice, as two versions.
        scope : Sequence[str], optional
            Ordered scope labels every file is placed under. Used with a list
            of paths; with a mapping, each file already has its scope and this
            argument is ignored.
        custom_metadata : Mapping[str, str], optional
            Metadata kept with every uploaded version.
        timeout : float, optional
            Seconds to wait for the platform's answer.

        Returns
        -------
        list[RagInputBatchItemResult]
            One result per file, in the given order. ``status`` is ``"ok"`` for
            a stored file and ``"error"`` for a rejected one, whose reason is
            in ``detail``.

        Raises
        ------
        ValueError
            No files were given.
        FileNotFoundError, IsADirectoryError
            A path does not exist, or is a folder.
        InvalidFileScopeError
            A scope breaks the platform's rules. Normally raised before
            sending, since the SDK applies the platform's rules first.
        FileBatchTooLargeError
            More than 100 files, or more than 2 GiB in total. Normally raised
            before sending.
        InvalidFileMetadataError
            The platform rejected ``custom_metadata``.
        ServiceError
            Any other error answer from the platform.
        """
        given = _pair_files_with_scopes(files, scope)
        if not given:
            raise ValueError("There are no files to upload.")
        scoped_files: list[ScopedFile] = []
        for path, file_scope in given:
            _check_scope(file_scope)
            scoped_files.append((_require_file(Path(path)), tuple(file_scope)))
        file_paths = [file_path for file_path, _ in scoped_files]
        _check_batch_limits(file_paths)

        # The manifest tells the platform each file's name and scope. Its
        # ``file`` index points at the matching ``files`` part below.
        manifest_entries = []
        for index, (file_path, file_scope) in enumerate(scoped_files):
            manifest_entries.append({"file": index, "name": file_path.name, "scope": file_scope})
        manifest = json.dumps(manifest_entries)

        def build_batch_fields(open_files: ExitStack) -> FormFields:
            """Build the form fields again for each attempt.

            A multipart file stream is consumed when sent, so a retry has to
            reopen the files. See ``_send_multipart``.
            """
            fields: FormFields = [("manifest", manifest)]
            if custom_metadata is not None:
                fields.append(("custom_metadata", json.dumps(dict(custom_metadata))))
            for file_path in file_paths:
                handle = open_files.enter_context(file_path.open("rb"))
                content_type = _guess_content_type(file_path.name)
                fields.append(("files", (file_path.name, handle, content_type)))
            return fields

        body = self._send_multipart(f"{self._path}/batch", build_batch_fields, timeout)
        response = RagInputBatchUploadResponse.model_validate(body)
        return response.results

    def upload_folder(
        self,
        folder: FilePath,
        *,
        scope: Scope = (),
        custom_metadata: Mapping[str, str] | None = None,
        timeout: float = UPLOAD_TIMEOUT,
    ) -> list[RagInputBatchItemResult]:
        """Upload the files directly inside a folder, all under one scope.

        Only the folder's own files are taken; subfolders and their contents
        are ignored. Otherwise this is :meth:`upload_files` with the folder's
        files, so the same limits and errors apply.

        Parameters
        ----------
        folder : str or os.PathLike
            Folder whose files to upload.
        scope : Sequence[str], optional
            Ordered scope labels every file is placed under.
        custom_metadata : Mapping[str, str], optional
            Metadata kept with every uploaded version.
        timeout : float, optional
            Seconds to wait for the platform's answer.

        Returns
        -------
        list[RagInputBatchItemResult]
            One result per file, in alphabetical order of the file names.

        Raises
        ------
        NotADirectoryError
            ``folder`` does not exist, or is not a folder.
        ValueError
            The folder holds no files.
        InvalidFileScopeError, FileBatchTooLargeError, InvalidFileMetadataError, ServiceError
            As in :meth:`upload_files`.
        """
        folder_path = Path(folder)
        if not folder_path.is_dir():
            raise NotADirectoryError(f"{str(folder_path)!r} is not a folder.")
        # ``iterdir`` does not descend into subfolders; sorting makes the order
        # of the results predictable.
        file_paths = sorted(entry for entry in folder_path.iterdir() if entry.is_file())
        return self.upload_files(
            file_paths, scope=scope, custom_metadata=custom_metadata, timeout=timeout
        )

    def _send_multipart(
        self,
        endpoint: str,
        build_fields: Callable[[ExitStack], FormFields],
        timeout: float,
    ) -> Any:
        """Post a multipart body to ``endpoint`` and return the parsed reply.

        ``build_fields`` opens the files it needs through the ``ExitStack`` it
        is given and returns the form fields. It is called once per attempt:
        a streamed body can be sent only once, so if the request is retried
        after a ``401`` the files have to be reopened and the body rebuilt.
        """
        # One boundary for every attempt, so the header, sent once, matches
        # each body that is built.
        boundary = uuid.uuid4().hex
        content_type = f"multipart/form-data; boundary={boundary}"

        # The stack collects every file handle opened for this request, however
        # many, and closes them all when the request is over.
        with ExitStack() as open_files:

            def build_body() -> MultipartEncoder:
                # Release the previous attempt's files before opening them again.
                open_files.close()
                fields = build_fields(open_files)
                # The encoder reads from the open handles while the request is
                # being sent, so the files stream from disk and are never held
                # in memory as a whole.
                return MultipartEncoder(fields=fields, boundary=boundary)

            try:
                # ``build_body`` is passed uncalled: ``send_request`` calls it
                # once per attempt.
                return self._communication.send_request(
                    "post",
                    endpoint,
                    data=build_body,
                    headers={"content-type": content_type},
                    timeout=timeout,
                )
            except ServiceError as exc:
                # Only the batch endpoint has a size limit, so only there does
                # a 413 mean "too much in one request".
                is_batch = endpoint.endswith("/batch")
                translated = _translate_error(exc, is_batch=is_batch)
                if translated is None:
                    raise
                raise translated from exc


# --------------------------------------------------------------------------- local checks


def _require_file(path: Path) -> Path:
    """Return ``path`` if it is an existing file; otherwise say what it is instead."""
    if path.is_dir():
        raise IsADirectoryError(f"{str(path)!r} is a folder; upload folders with upload_folder.")
    if not path.is_file():
        raise FileNotFoundError(f"{str(path)!r} does not exist.")
    return path


def _check_scope(scope: Scope) -> None:
    """Raise :class:`InvalidFileScopeError` if the platform would reject ``scope``."""
    # A string is a sequence of characters, so ``scope="legal"`` would silently
    # become the labels l, e, g, a, l. Catch that mistake by name.
    if isinstance(scope, str):
        raise InvalidFileScopeError(
            f"A scope is a list of labels, not a string; did you mean [{scope!r}]?",
            status_code=400,
        )
    labels = list(scope)
    if len(labels) > SCOPE_MAX_LABELS:
        raise InvalidFileScopeError(
            f"A scope has at most {SCOPE_MAX_LABELS} labels, got {len(labels)}.",
            status_code=400,
        )
    combined_length = sum(len(label) for label in labels)
    if combined_length > SCOPE_TOTAL_MAX_LENGTH:
        raise InvalidFileScopeError(
            f"Scope labels combined exceed {SCOPE_TOTAL_MAX_LENGTH} characters.",
            status_code=400,
        )
    for label in labels:
        is_valid_length = 0 < len(label) <= SCOPE_LABEL_MAX_LENGTH
        if not (is_valid_length and _SCOPE_LABEL_PATTERN.fullmatch(label)):
            raise InvalidFileScopeError(
                f"Scope label {label!r} must be 1 to {SCOPE_LABEL_MAX_LENGTH} characters of "
                "letters, digits, underscores and hyphens.",
                status_code=400,
            )


def _pair_files_with_scopes(
    files: Iterable[FilePath] | Mapping[FilePath, Scope],
    scope: Scope,
) -> list[tuple[FilePath, Scope]]:
    """Return each file with the scope it goes to, in the order given, unchecked.

    A mapping carries its own scope per file and wins over ``scope``.
    """
    if isinstance(files, Mapping):
        return list(files.items())
    return [(path, scope) for path in files]


def _check_batch_limits(file_paths: list[Path]) -> None:
    """Raise if ``file_paths`` exceed what one request to the batch endpoint carries.

    The status codes are the ones the platform would answer with.
    """
    if len(file_paths) > BATCH_MAX_FILES:
        raise FileBatchTooLargeError(
            f"One request carries at most {BATCH_MAX_FILES} files, got {len(file_paths)}. "
            "Split the files across several calls.",
            status_code=400,
        )
    total_bytes = 0
    for file_path in file_paths:
        total_bytes += file_path.stat().st_size
    if total_bytes > BATCH_MAX_BYTES:
        raise FileBatchTooLargeError(
            f"One request carries at most {BATCH_MAX_BYTES} bytes, these files total "
            f"{total_bytes}. Split the files across several calls.",
            status_code=413,
        )


# --------------------------------------------------------------------------- request


def _guess_content_type(file_name: str) -> str:
    """Return the MIME type for ``file_name``; the platform guesses the same way."""
    guessed_type, _ = mimetypes.guess_type(file_name)
    return guessed_type or _FALLBACK_CONTENT_TYPE


def _translate_error(exc: ServiceError, *, is_batch: bool) -> ServiceError | None:
    """Return the named exception for an upload error answer, or ``None`` if unknown.

    ``Communication`` formats every error as ``METHOD path failed with CODE:
    detail``. Only the platform's detail is inspected, so a database whose
    name happens to contain a keyword cannot change the outcome.
    """
    message = str(exc)
    _, _, detail = message.partition(f"failed with {exc.status_code}: ")
    codes = {"status_code": exc.status_code, "error_code": exc.error_code}

    if exc.status_code == 400 and "scope" in detail:
        return InvalidFileScopeError(message, **codes)
    if exc.status_code == 400 and "custom_metadata" in detail:
        return InvalidFileMetadataError(message, **codes)
    if exc.status_code == 413 and is_batch:
        return FileBatchTooLargeError(message, **codes)
    if exc.status_code == 422 and "cannot be empty" in detail:
        return EmptyFileError(message, **codes)
    # Only the platform's own storage failure promises a rollback; a 500 from
    # somewhere in between says nothing about what was stored.
    is_storage_failure = "rolled back" in detail or "internal error" in detail
    if exc.status_code == 500 and is_storage_failure:
        return FileUploadFailedError(message, **codes)
    return None
