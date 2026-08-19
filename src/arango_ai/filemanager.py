"""File Manager wrappers: RAG input files (batch upload, list, delete).

Gateway prefix /_platform/filemanager (ArangoRoute for the file-manager
service); bodies are snake_case. A file lives at a "scope", an ordered list
of labels that works like a folder path. The SDK mirrors AutoGraph Studio's
layout — scope[0] is the project, the optional scope[1] a category — so SDK
uploads land exactly where the Studio wizard looks.

The batch endpoint rejects a WHOLE request over its file-count/byte caps,
after the body has already been uploaded, so uploads are chunked client-side
and each chunk fails independently. Unlike the Studio, the SDK also sends
per-file custom_metadata (e.g. citable_url) through the manifest; the
backend stores and returns it end to end (AIS-1740).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Sequence
from urllib.parse import quote

import httpx

from .exceptions import ConfigError
from .http import error_detail, raise_for_status

FILE_MANAGER_BASE = "/_platform/filemanager"

# Chunk caps mirror the tightest deployed server bounds (file manager
# app/utils/batch_upload.py). Staying under them keeps one oversized call
# from becoming an all-or-nothing rejection for every file in it.
BATCH_MAX_FILES = 100
BATCH_MAX_BYTES = 512 * 1024 * 1024

# The corpus build's file parser rejects files over 100 MB. The File Manager
# itself would store them fine, so without this check an oversized file
# uploads now and fails much later, mid-build.
MAX_PARSER_FILE_BYTES = 100 * 1024 * 1024

# What the corpus build can parse; anything else found by a folder walk is
# reported as skipped instead of uploaded-then-ignored.
ACCEPTED_EXTENSIONS = {".txt", ".md", ".pdf", ".doc", ".docx", ".ppt", ".pptx"}

# Subfolder paths are flattened into the stored name with "__" rather than
# kept as "/": the name travels beyond the File Manager (corpus builds, KG
# provenance), where a path-like name could trip consumers that split on or
# normalize slashes.
UPLOAD_PATH_SEPARATOR = "__"

# Scope labels participate in colon-delimited file ids and dot-delimited
# metadata keys, so the charset must stay colon- and dot-free. Matches the
# server's validator and the Studio's category-name rule.
_LABEL_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,128}")

# --- ArangoDB document-key budget (mirrors the Studio's autographWizard) ----
# File metadata lives under a document key
#   _rag_input.<db>.<label>….rag-input-<base64(":<n>:<db>:<label>:…:<name>")>.v<v>
# and ArangoDB caps keys at 254 characters. Over the cap the server fails the
# file with an opaque per-file 500 — deterministically, so retrying can never
# succeed. The SDK refuses the combination up front instead.
_ARANGO_KEY_MAX = 254
# ".v1" on first upload, but the version grows when a file is overwritten —
# leave room up to .v999 rather than storing v1 fine and failing an
# overwrite later.
_VERSION_SUFFIX_HEADROOM = 5

_ParamValue = str | int | float | bool | None


@dataclass
class FileUpload:
    """One file to upload: stored name, raw bytes, optional metadata.

    custom_metadata is stored with the uploaded version and returned on
    get/list (e.g. a citable_url for provenance). Included in the manifest
    only when set, so uploads without it stay byte-identical to the Studio's.
    """

    name: str
    content: bytes
    custom_metadata: dict[str, str] | None = None


@dataclass
class UploadResult:
    """Aggregated outcome of one upload call across all chunks.

    ok and failed carry the server's per-file result dicts (client-side
    failures are synthesized in the same shape). skipped lists folder-walk
    files refused for an unsupported extension — deliberate non-errors.
    """

    ok: list[dict[str, Any]]
    failed: list[dict[str, Any]]
    skipped: list[str] = field(default_factory=list)


def _validate_label(kind: str, value: str) -> str:
    if _LABEL_PATTERN.fullmatch(value) is None:
        raise ConfigError(
            f"invalid {kind} {value!r}: use 1-128 letters, digits, hyphens or "
            "underscores (no spaces)"
        )
    return value


def _sanitize_label(name: str) -> str:
    """Folder name to scope-safe label, mirroring the Studio's sanitizer."""
    collapsed = re.sub(r"[^A-Za-z0-9_-]+", "-", name.strip())
    return collapsed.strip("-")[:128]


def _over_key_budget(database: str, scope: Sequence[str], name: str) -> bool:
    dotted_prefix = len(".".join(["_rag_input", database, *scope])) + 1
    encoded = len(f":{len(scope)}:{database}:{':'.join(scope)}:".encode())
    encoded += len(name.encode())
    budget = (
        _ARANGO_KEY_MAX - dotted_prefix - len("rag-input-") - _VERSION_SUFFIX_HEADROOM
    )
    # Unpadded base64 length of n input bytes is ceil(4n / 3).
    return (4 * encoded + 2) // 3 > budget


def _failure(name: str, scope: Sequence[str], detail: str) -> dict[str, Any]:
    return {"name": name, "scope": list(scope), "status": "error", "detail": detail}


def _pack_chunks(files: Sequence[FileUpload]) -> list[list[FileUpload]]:
    """Greedy in-order packing under both request caps.

    A file bigger than BATCH_MAX_BYTES still ships, alone in its chunk — the
    server's real cap is higher, and if the file exceeds that too only that
    chunk fails.
    """
    chunks: list[list[FileUpload]] = []
    current: list[FileUpload] = []
    current_bytes = 0
    for upload in files:
        closes = len(current) >= BATCH_MAX_FILES or (
            len(current) > 0 and current_bytes + len(upload.content) > BATCH_MAX_BYTES
        )
        if closes:
            chunks.append(current)
            current = []
            current_bytes = 0
        current.append(upload)
        current_bytes += len(upload.content)
    if current:
        chunks.append(current)
    return chunks


def _manifest(scope: Sequence[str], chunk: Sequence[FileUpload]) -> str:
    entries: list[dict[str, Any]] = []
    for index, upload in enumerate(chunk):
        entry: dict[str, Any] = {
            "file": index,
            "scope": list(scope),
            "name": upload.name,
        }
        if upload.custom_metadata:
            entry["custom_metadata"] = upload.custom_metadata
        entries.append(entry)
    return json.dumps(entries)


def _chunk_error_detail(response: httpx.Response) -> str:
    """Server message for a whole-chunk rejection.

    The file manager is FastAPI and wraps errors as {"detail": ...}; the
    shared error_detail knows the gateway's {"error"/"message"} shapes and
    stays as the fallback.
    """
    try:
        body = response.json()
    except ValueError:
        body = None
    if isinstance(body, dict):
        detail = body.get("detail")
        if isinstance(detail, str) and detail:
            return detail
    return error_detail(response)


def _is_accepted(filename: str) -> bool:
    dot = filename.rfind(".")
    return dot >= 0 and filename[dot:].lower() in ACCEPTED_EXTENSIONS


def _dedupe_name(name: str, taken: set[str]) -> str:
    """Suffix duplicates "name (2).ext"-style.

    The store keys a file by (scope, name), so a duplicate would silently
    become a hidden new version of the first file instead of a second file.
    """
    if name not in taken:
        return name
    dot = name.rfind(".")
    stem, ext = (name[:dot], name[dot:]) if dot > 0 else (name, "")
    counter = 2
    while f"{stem} ({counter}){ext}" in taken:
        counter += 1
    return f"{stem} ({counter}){ext}"


def _iter_visible_files(root: Path) -> Iterator[Path]:
    """Walk recursively; hidden files and directories (leading dot) are
    pruned silently — noise the user didn't consciously pick. Sorted so
    upload order and dedupe suffixes are deterministic."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for filename in sorted(filenames):
            if not filename.startswith("."):
                yield Path(dirpath) / filename


def _collect_folder(root: Path) -> tuple[list[FileUpload], list[str], list[str]]:
    """Folder contents as (uploads, skipped names, oversized names)."""
    uploads: list[FileUpload] = []
    skipped: list[str] = []
    oversized: list[str] = []
    taken: set[str] = set()
    for path in _iter_visible_files(root):
        name = UPLOAD_PATH_SEPARATOR.join(path.relative_to(root).parts)
        if not _is_accepted(path.name):
            skipped.append(name)
            continue
        if path.stat().st_size > MAX_PARSER_FILE_BYTES:
            oversized.append(name)
            continue
        name = _dedupe_name(name, taken)
        taken.add(name)
        uploads.append(FileUpload(name=name, content=path.read_bytes()))
    return uploads, skipped, oversized


def _rag_base(database: str) -> str:
    # The database is a caller-supplied path segment; quote it like the
    # Studio's encodeURIComponent so odd names cannot derail the route.
    return f"{FILE_MANAGER_BASE}/_db/{quote(database, safe='')}/rag-input"


def _build_scope(project: str, category: str | None) -> list[str]:
    scope = [_validate_label("project", project)]
    if category is not None:
        scope.append(_validate_label("category", category))
    return scope


def _key_budget_split(
    database: str, scope: Sequence[str], files: Sequence[FileUpload]
) -> tuple[list[FileUpload], list[dict[str, Any]]]:
    """Files split into (sendable, up-front key-budget failures)."""
    sendable: list[FileUpload] = []
    failed: list[dict[str, Any]] = []
    for upload in files:
        if _over_key_budget(database, scope, upload.name):
            failed.append(
                _failure(
                    upload.name,
                    scope,
                    "file name too long for this scope: the derived "
                    f"metadata key would exceed ArangoDB's "
                    f"{_ARANGO_KEY_MAX}-character key cap; "
                    "shorten the name",
                )
            )
        else:
            sendable.append(upload)
    return sendable, failed


def _chunk_parts(
    chunk: Sequence[FileUpload],
) -> list[tuple[str, tuple[str, bytes, str]]]:
    return [
        ("files", (upload.name, upload.content, "application/octet-stream"))
        for upload in chunk
    ]


def _chunk_outcome(
    response: httpx.Response, scope: Sequence[str], chunk: Sequence[FileUpload]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """One chunk POST's response as (ok, failed) per-file results.

    A whole-chunk rejection (400 malformed / 413 too large / 500) fails
    only this chunk's files; later chunks still get their shot.
    """
    if response.status_code >= 400:
        detail = _chunk_error_detail(response)
        return [], [_failure(upload.name, scope, detail) for upload in chunk]
    # 200 = all ok, 207 = partial; either way per-file statuses decide.
    ok: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    for item in response.json().get("results") or []:
        (ok if item.get("status") == "ok" else failed).append(dict(item))
    return ok, failed


def _folder_upload_plan(
    project: str, folder: str | Path, category: str | None
) -> tuple[str, list[FileUpload], list[str], list[dict[str, Any]]]:
    """Everything about a folder upload except the HTTP: the resolved
    category label, collected uploads, skipped names, and the up-front
    failures for oversized files."""
    root = Path(folder)
    if not root.is_dir():
        raise ConfigError(f"upload_folder needs a directory, got {str(root)!r}")
    label = _sanitize_label(root.name) if category is None else category
    if not label:
        raise ConfigError(
            f"folder name {root.name!r} does not yield a usable category "
            "label; pass category="
        )
    uploads, skipped, oversized = _collect_folder(root)
    oversized_failures = [
        _failure(
            name,
            [project, label],
            f"file exceeds {MAX_PARSER_FILE_BYTES} bytes; the corpus "
            "build's parser rejects larger files, so it is not uploaded",
        )
        for name in oversized
    ]
    return label, uploads, skipped, oversized_failures


def _list_params(
    scope: Sequence[str],
    search: str | None,
    name: str | None,
    limit: int,
    offset: int,
) -> list[tuple[str, _ParamValue]]:
    params: list[tuple[str, _ParamValue]] = [("scope", label) for label in scope]
    if search is not None:
        params.append(("search", search))
    if name is not None:
        params.append(("name", name))
    params.extend((("limit", limit), ("offset", offset)))
    return params


def _categories_of(payload: dict[str, Any]) -> list[tuple[str, int]]:
    children = payload.get("children") or []
    return [(child["segment"], child["file_count"]) for child in children]


def _grouped_delete_results(payload: dict[str, Any]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {"deleted": [], "locked": [], "not_found": []}
    for item in payload.get("results") or []:
        status = item.get("status")
        if status in grouped:
            grouped[status].append(item["id"])
    return grouped


def _scope_delete_outcome(body: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "deleted": list(body.get("deleted") or []),
        "locked": list(body.get("locked") or []),
    }


class FileManagerAPI:
    """Low-level File Manager calls, one method per endpoint plus chunking."""

    def __init__(self, http: httpx.Client, database: str) -> None:
        self._http = http
        self._database = database

    @property
    def database(self) -> str:
        return self._database

    @property
    def _base(self) -> str:
        return _rag_base(self._database)

    # -- upload --------------------------------------------------------------

    def upload(
        self,
        project: str,
        files: Sequence[FileUpload],
        *,
        category: str | None = None,
    ) -> UploadResult:
        """Upload files under [project] or [project, category].

        Chunks POST sequentially with no auto-retry. Any failure — a bad
        file inside a 207, a rejected chunk — lands per file in `failed`
        and the remaining chunks still upload, so callers get one uniform
        partial-success shape to drive retry from.
        """
        scope = _build_scope(project, category)
        sendable, budget_failures = _key_budget_split(self._database, scope, files)
        result = UploadResult(ok=[], failed=budget_failures)
        for chunk in _pack_chunks(sendable):
            response = self._http.post(
                f"{self._base}/batch",
                files=_chunk_parts(chunk),
                data={"manifest": _manifest(scope, chunk)},
            )
            ok, failed = _chunk_outcome(response, scope, chunk)
            result.ok.extend(ok)
            result.failed.extend(failed)
        return result

    def upload_folder(
        self,
        project: str,
        folder: str | Path,
        *,
        category: str | None = None,
    ) -> UploadResult:
        """Upload a folder recursively as one category.

        Mirrors the Studio's folder drop: unsupported extensions are skipped
        (reported, not errors), hidden files and directories are pruned,
        subfolder paths are flattened into the stored name, duplicate names
        are suffixed, and files over MAX_PARSER_FILE_BYTES fail up front —
        the corpus build would reject them much later otherwise. The default
        category is the sanitized folder name.
        """
        label, uploads, skipped, oversized = _folder_upload_plan(
            project, folder, category
        )
        result = self.upload(project, uploads, category=label)
        result.failed.extend(oversized)
        result.skipped.extend(skipped)
        return result

    # -- listing --------------------------------------------------------------

    def list_files(
        self,
        project: str,
        *,
        category: str | None = None,
        search: str | None = None,
        name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List files at the scope and below (latest version each).

        `search` is a case-insensitive substring match on the name, `name`
        an exact match; all filters combine (AND).
        """
        params = _list_params(
            _build_scope(project, category), search, name, limit, offset
        )
        response = raise_for_status(self._http.get(self._base, params=params))
        return dict(response.json())

    def list_categories(self, project: str) -> list[tuple[str, int]]:
        """Immediate child scopes of the project with active-file counts."""
        _validate_label("project", project)
        response = raise_for_status(
            self._http.get(f"{self._base}/scopes", params=[("scope", project)])
        )
        return _categories_of(response.json())

    # -- deletion --------------------------------------------------------------

    def delete_files(self, ids: Sequence[str]) -> dict[str, list[str]]:
        """Delete files by id (all versions each), grouped by outcome.

        not_found is reported, not dropped (the Studio drops it): a scripted
        cleanup needs to see which targeted ids no longer exist. locked ids
        are baked into a built corpus (safe_to_delete=false) and are kept.
        """
        if not ids:
            return _grouped_delete_results({})
        response = raise_for_status(
            self._http.post(f"{self._base}/delete", json={"ids": list(ids)})
        )
        return _grouped_delete_results(response.json())

    def delete_category(self, project: str, category: str) -> dict[str, list[str]]:
        """Delete every deletable file under [project, category].

        Locked files are reported and kept (200 all deleted / 207 partial).
        """
        scope = _build_scope(project, category)
        response = raise_for_status(
            self._http.post(f"{self._base}/delete-scope", json={"scope": scope})
        )
        return _scope_delete_outcome(response.json())


class AsyncFileManagerAPI:
    """Async twin of FileManagerAPI: same chunking, manifests, and shapes.

    Local file-system work (the folder walk, read_bytes) deliberately stays
    synchronous also here: alpha-scale corpora read in milliseconds and the
    chunk uploads dominate; a thread offload would buy nothing yet.
    """

    def __init__(self, http: httpx.AsyncClient, database: str) -> None:
        self._http = http
        self._database = database

    @property
    def database(self) -> str:
        return self._database

    @property
    def _base(self) -> str:
        return _rag_base(self._database)

    # -- upload --------------------------------------------------------------

    async def upload(
        self,
        project: str,
        files: Sequence[FileUpload],
        *,
        category: str | None = None,
    ) -> UploadResult:
        """Async twin of FileManagerAPI.upload (sequential chunks, no retry)."""
        scope = _build_scope(project, category)
        sendable, budget_failures = _key_budget_split(self._database, scope, files)
        result = UploadResult(ok=[], failed=budget_failures)
        for chunk in _pack_chunks(sendable):
            response = await self._http.post(
                f"{self._base}/batch",
                files=_chunk_parts(chunk),
                data={"manifest": _manifest(scope, chunk)},
            )
            ok, failed = _chunk_outcome(response, scope, chunk)
            result.ok.extend(ok)
            result.failed.extend(failed)
        return result

    async def upload_folder(
        self,
        project: str,
        folder: str | Path,
        *,
        category: str | None = None,
    ) -> UploadResult:
        """Async twin of FileManagerAPI.upload_folder."""
        label, uploads, skipped, oversized = _folder_upload_plan(
            project, folder, category
        )
        result = await self.upload(project, uploads, category=label)
        result.failed.extend(oversized)
        result.skipped.extend(skipped)
        return result

    # -- listing --------------------------------------------------------------

    async def list_files(
        self,
        project: str,
        *,
        category: str | None = None,
        search: str | None = None,
        name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Async twin of FileManagerAPI.list_files."""
        params = _list_params(
            _build_scope(project, category), search, name, limit, offset
        )
        response = raise_for_status(await self._http.get(self._base, params=params))
        return dict(response.json())

    async def list_categories(self, project: str) -> list[tuple[str, int]]:
        """Async twin of FileManagerAPI.list_categories."""
        _validate_label("project", project)
        response = raise_for_status(
            await self._http.get(f"{self._base}/scopes", params=[("scope", project)])
        )
        return _categories_of(response.json())

    # -- deletion --------------------------------------------------------------

    async def delete_files(self, ids: Sequence[str]) -> dict[str, list[str]]:
        """Async twin of FileManagerAPI.delete_files."""
        if not ids:
            return _grouped_delete_results({})
        response = raise_for_status(
            await self._http.post(f"{self._base}/delete", json={"ids": list(ids)})
        )
        return _grouped_delete_results(response.json())

    async def delete_category(
        self, project: str, category: str
    ) -> dict[str, list[str]]:
        """Async twin of FileManagerAPI.delete_category."""
        scope = _build_scope(project, category)
        response = raise_for_status(
            await self._http.post(f"{self._base}/delete-scope", json={"scope": scope})
        )
        return _scope_delete_outcome(response.json())
