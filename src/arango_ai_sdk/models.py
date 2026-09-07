"""Data classes shared between the SDK and the platform services.

The classes are generated from the ``.proto`` files under ``proto/`` into the
private ``_proto_out`` package by ``make generate-proto``. That package is
regenerated wholesale, so nothing hand-written can live there. This module is
the single hand-written seam over it: it names the types the SDK supports and
nothing else, so the rest of the SDK, and users, import from here and never
from the generated code.

Replacing a generated type with an SDK-owned one later changes this file only.
"""

from arango_ai_sdk._proto_out.project_metadata import AiProject, CreateProjectRequest
from arango_ai_sdk._proto_out.secrets import Profile, ProfileType

__all__ = ["AiProject", "CreateProjectRequest", "Profile", "ProfileType"]
