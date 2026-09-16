"""Data classes shared between the SDK and the platform services.

The classes are generated, never written by hand. The ACP ones come from the
``.proto`` files under ``proto/`` into the private ``_proto_out`` package by
``make generate-proto``; the file service ones come from the OpenAPI documents
under ``specs/`` into the private ``_openapi_out`` package by
``make generate-openapi``. Both packages are regenerated wholesale, so nothing
hand-written can live there. This module is the single hand-written seam over
them: it names the types the SDK supports and nothing else, so the rest of the
SDK, and users, import from here and never from the generated code.

Replacing a generated type with an SDK-owned one later changes this file only.
"""

from arango_ai_sdk._openapi_out.rag_input import (
    RagInputBatchItemResult,
    RagInputBatchUploadResponse,
    RagInputUploadResponse,
    ScopeSegment,
)
from arango_ai_sdk._proto_out.genai import CreateEntityRequest, ServiceInfo, ServiceMeta
from arango_ai_sdk._proto_out.project_metadata import (
    AiProject,
    AutoGraphModelSettings,
    AutoGraphService,
    CreateProjectRequest,
    GetProjectByNameRequest,
    GraphRagProjectMetaData,
)
from arango_ai_sdk._proto_out.secrets import (
    CreateSecretProfileRequest,
    Profile,
    ProfileType,
)

__all__ = [
    "AiProject",
    "AutoGraphModelSettings",
    "AutoGraphService",
    "CreateEntityRequest",
    "CreateProjectRequest",
    "CreateSecretProfileRequest",
    "GetProjectByNameRequest",
    "GraphRagProjectMetaData",
    "Profile",
    "ProfileType",
    "RagInputBatchItemResult",
    "RagInputBatchUploadResponse",
    "RagInputUploadResponse",
    "ScopeSegment",
    "ServiceInfo",
    "ServiceMeta",
]
