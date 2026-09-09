"""Data classes shared between the SDK and the platform services.

Most classes are generated from the ``.proto`` files under ``proto/`` into the
private ``_proto_out`` package by ``make generate-proto``. That package is
regenerated wholesale, so nothing hand-written can live there. This module is
the single hand-written seam over it: it names the types the SDK supports and
nothing else, so the rest of the SDK, and users, import from here and never
from the generated code.

Replacing a generated type with an SDK-owned one later changes this file only.

The file upload classes are SDK-owned. The file service publishes its API as an
OpenAPI document rather than a proto, so there is nothing to generate them from;
they mirror the response bodies field for field.
"""

from dataclasses import dataclass, field
from datetime import datetime

from arango_ai_sdk._proto_out.project_metadata import AiProject, CreateProjectRequest
from arango_ai_sdk._proto_out.secrets import Profile, ProfileType

__all__ = [
    "AiProject",
    "BatchItemResult",
    "BatchUploadResult",
    "CreateProjectRequest",
    "Profile",
    "ProfileType",
    "UploadedFile",
]


@dataclass(frozen=True)
class UploadedFile:
    """One stored file version, as the platform described it after an upload.

    Attributes
    ----------
    id : str
        Identifier of the file. It encodes the database, the scope and the
        name, so every version of the same file shares it.
    name : str
        File name within its scope.
    database : str
        Database the file is stored in.
    scope : tuple[str, ...]
        Ordered scope labels, empty for a file at the database root.
    content_type : str
        MIME type the platform detected.
    size : int
        Stored size in bytes.
    uploaded_at : datetime
        When this version was stored, timezone-aware.
    version : int
        Version number, starting at 1. Uploading the same name under the same
        scope again produces the next version rather than a new file.
    safe_to_delete : bool
        Whether the file may be deleted. New uploads start as ``True``; the
        ingestion locks a file by setting it to ``False`` once a built graph
        depends on it.
    metadata_key : str
        Key of the file's metadata record on the platform.
    custom_metadata : dict[str, str]
        The metadata given at upload, or empty.
    """

    id: str
    name: str
    database: str
    scope: tuple[str, ...]
    content_type: str
    size: int
    uploaded_at: datetime
    version: int
    safe_to_delete: bool
    metadata_key: str
    custom_metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class BatchItemResult:
    """Outcome for one file of a batch upload.

    A batch is processed file by file, and one file failing does not stop the
    others. Check :attr:`ok` before reading the storage attributes, which are
    ``None`` for a failed item.

    Attributes
    ----------
    name : str
        File name within its scope.
    scope : tuple[str, ...]
        Scope the file was sent to.
    status : str
        ``"ok"`` when stored, ``"error"`` otherwise.
    detail : str or None
        Why the file failed, for a failed item.
    id, version, content_type, size, uploaded_at, metadata_key, custom_metadata
        As in :class:`UploadedFile`, for a stored item.
    """

    name: str
    scope: tuple[str, ...]
    status: str
    detail: str | None = None
    id: str | None = None
    version: int | None = None
    content_type: str | None = None
    size: int | None = None
    uploaded_at: datetime | None = None
    metadata_key: str | None = None
    custom_metadata: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """Whether this file was stored."""
        return self.status == "ok"


@dataclass(frozen=True)
class BatchUploadResult:
    """Outcome of a multi-file upload.

    Large sets are sent in several requests; this object aggregates them, so
    the counts and results cover every file that was given.

    Attributes
    ----------
    database : str
        Database the files were sent to.
    results : list[BatchItemResult]
        One entry per file, in the order the files were given.
    ok_count : int
        Number of files stored.
    error_count : int
        Number of files that failed. Their reasons are in :attr:`results`.
    """

    database: str
    results: list[BatchItemResult]
    ok_count: int
    error_count: int

    @property
    def failed(self) -> list[BatchItemResult]:
        """The results of the files that were not stored."""
        return [item for item in self.results if not item.ok]
