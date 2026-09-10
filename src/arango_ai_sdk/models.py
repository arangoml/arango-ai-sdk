"""Data classes shared between the SDK and the platform services.

Most classes are generated from the ``.proto`` files under ``proto/`` into the
private ``_proto_out`` package by ``make generate-proto``. That package is
regenerated wholesale, so nothing hand-written can live there. This module is
the single hand-written seam over it: it names the types the SDK supports and
nothing else, so the rest of the SDK, and users, import from here and never
from the generated code.

Replacing a generated type with an SDK-owned one later changes this file only.

The file upload classes are SDK-owned. The file service publishes its API as an
OpenAPI document rather than a proto, so there is nothing to generate them from.
:class:`UploadedFile` mirrors the stored-file object the service returns;
:class:`FileUploadResult` wraps it for multi-file uploads, where each file is
reported separately and may have failed.
"""

from dataclasses import dataclass, field
from datetime import datetime

from arango_ai_sdk._proto_out.project_metadata import (
    AiProject,
    AutoGraphModelSettings,
    CreateProjectRequest,
    GetProjectByNameRequest,
    GraphRagProjectMetaData,
)
from arango_ai_sdk._proto_out.secrets import CreateSecretProfileRequest, Profile, ProfileType

__all__ = [
    "AiProject",
    "AutoGraphModelSettings",
    "CreateProjectRequest",
    "CreateSecretProfileRequest",
    "FileUploadResult",
    "GetProjectByNameRequest",
    "GraphRagProjectMetaData",
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
class FileUploadResult:
    """Outcome for one file of a multi-file upload.

    A multi-file upload is not all-or-nothing: the platform stores the files
    one by one and reports each separately, so one file can fail while the
    others are stored. This class is therefore a wrapper around
    :class:`UploadedFile` rather than a variant of it. When the file was
    stored, :attr:`file` is the same :class:`UploadedFile` a single upload
    returns; when it failed, there is no stored file to describe and
    :attr:`file` is ``None``, with the reason in :attr:`detail`.

    :attr:`name` and :attr:`scope` are always set, so a result can be reported
    without checking :attr:`ok` first. For a stored file they repeat
    ``file.name`` and ``file.scope``.

    Attributes
    ----------
    name : str
        File name within its scope.
    scope : tuple[str, ...]
        Scope the file was sent to.
    file : UploadedFile or None
        The stored version, or ``None`` if the platform rejected the file.
    detail : str or None
        Why the file was rejected, or ``None`` if it was stored.
    """

    name: str
    scope: tuple[str, ...]
    file: UploadedFile | None
    detail: str | None

    @property
    def ok(self) -> bool:
        """Whether this file was stored."""
        return self.file is not None
