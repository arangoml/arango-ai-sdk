"""Secret profile namespace.

A secret profile holds one secret which can be any secret value
the user wants to store and use later that the platform stores encrypted.
In the context of AutoGraph, it is an API key .
Later stages reference a profile by its ID instead of sending the
key itself: AutoGraph takes one profile ID for the chat model and one for the
embedding model.
"""

from collections.abc import Mapping
from typing import Any

from arango_ai_sdk._naming import AcpPath, SecretProfileKey
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import (
    InvalidSecretNameError,
    InvalidSecretValueError,
    SecretProfileNotFoundError,
    ServiceError,
)
from arango_ai_sdk.models import CreateSecretProfileRequest, Profile, ProfileType

__all__ = ["SecretProfileManager"]


class SecretProfileManager:
    """Create and fetch secret profiles through the communication layer.

    Parameters
    ----------
    communication : Communication
        Shared transport. This namespace calls ``send_request`` and nothing else.
    """

    _path = AcpPath.SECRETS

    def __init__(self, communication: Communication) -> None:
        self._communication = communication

    def create(
        self,
        name: str,
        secret: str,
        *,
        provider: str | None = None,
        description: str | None = None,
        profile_type: ProfileType = ProfileType.LLM,
    ) -> Profile:
        """Create a secret profile holding one secret and return it.

        Parameters
        ----------
        name : str
            Human-readable profile name. Letters, digits, spaces, underscores and
            hyphens, 1 to 63 characters. Validated by the service, not here.
        secret : str
            The secret to store, e.g. an API key. Sent once, then only ever
            referenced by the returned ``profile_id``. Never logged and never
            included in an exception message.
        provider : str, optional
            Provider the secret belongs to, e.g. ``"openai"``. Recommended so
            later stages can pick the right profile; not validated by the service.
        description : str, optional
            Free text, at most 1024 characters. Omitted from the request when not
            given.
        profile_type : ProfileType, optional
            Category of the profile. Defaults to ``ProfileType.LLM``, which is
            what AutoGraph expects for chat and embedding keys.

        Returns
        -------
        Profile
            The created profile. ``secret_data`` carries only an obfuscated copy
            of the secret; ``profile_id`` is what later stages need.

        Raises
        ------
        InvalidSecretNameError
            The service rejected ``name``.
        InvalidSecretValueError
            The service rejected ``secret`` (empty or longer than 4096 characters).
        ServiceError
            Any other error answer from the service.
        """
        # The request body comes from the generated proto message, so the field
        # names are the proto's and a rename breaks at import time, not on the
        # wire. `to_dict` emits camelCase keys, which the gateway accepts.
        # Note on empty strings: `to_dict` omits a plain string field at its zero
        # value, so name="" is not sent at all. The server reads a missing field
        # as "" anyway, so it still gets rejected with the same error.
        # description and provider are proto `optional` fields, so presence is
        # tracked: None is omitted, "" is sent as "".
        # The service expects the profile type by its proto name ("LLM").
        request = CreateSecretProfileRequest(
            profile_type=profile_type.name,
            name=name,
            secret_data=secret,
            description=description,
            provider=provider,
        )
        data = request.to_dict()
        invalid_secret_name_message = "Secret name can only contain"
        invalid_secret_value_empty_message = "Secret value cannot be empty"
        invalid_secret_value_length_message = "must not exceed 4096"
        try:
            body = self._communication.send_request("post", self._path, data=data)
        except ServiceError as exc:
            message = str(exc)
            if invalid_secret_name_message in message:
                raise InvalidSecretNameError(
                    message,
                    status_code=exc.status_code,
                    error_code=exc.error_code,
                ) from exc
            if (
                invalid_secret_value_empty_message in message
                or invalid_secret_value_length_message in message
            ):
                raise InvalidSecretValueError(
                    message,
                    status_code=exc.status_code,
                    error_code=exc.error_code,
                ) from exc
            raise
        return _profile_from_body(body["profile"])

    def get(self, profile_id: str) -> Profile:
        """Fetch an existing secret profile by its ID.

        Parameters
        ----------
        profile_id : str
            ID returned by :meth:`create`, or copied from the platform UI.

        Returns
        -------
        Profile
            The profile as the service returned it, secret obfuscated.

        Raises
        ------
        SecretProfileNotFoundError
            No profile with this ID exists, or ``profile_id`` is empty.
        ServiceError
            Any other error answer from the service.
        """
        if not profile_id:
            raise SecretProfileNotFoundError(
                "No secret profile with this ID exists.",
                status_code=404,
            )
        try:
            body = self._communication.send_request("get", f"{self._path}/{profile_id}")
        except ServiceError as exc:
            if exc.status_code == 404:
                raise SecretProfileNotFoundError(
                    str(exc),
                    status_code=exc.status_code,
                    error_code=exc.error_code,
                ) from exc
            raise
        return _profile_from_body(body["profile"])


def _profile_from_body(raw: Mapping[str, Any]) -> Profile:
    """Build a :class:`Profile` from the ``profile`` object of a service reply.

    The API shape differs from the stored proto in two places, so the body is
    adapted before it is loaded: the API sends ``secretData`` as one obfuscated
    string while ``Profile.secret_data`` is a map, and the API's top-level
    ``provider`` is kept by the service inside ``metadata``.

    Parameters
    ----------
    raw : Mapping[str, Any]
        The camelCase JSON object under ``"profile"``.

    Returns
    -------
    Profile
        The loaded profile.
    """
    data = dict(raw)
    # Put the provider back where the service keeps it, so the object matches
    # what is stored on the platform.
    provider = data.pop("provider", "")
    if provider:
        metadata = dict(data.get("metadata") or {})
        metadata[SecretProfileKey.PROVIDER_METADATA] = provider
        data["metadata"] = metadata
    # The API flattens the secret map to one obfuscated string; wrap it again
    # under the fixed key so it fits the map field.
    if "secretData" in data:
        data["secretData"] = {SecretProfileKey.SECRET_DATA: data["secretData"]}
    profile = Profile()
    # `from_dict` fills the instance in place and returns it. It is a betterproto
    # `hybridmethod` descriptor that ty cannot type, hence the ignore.
    profile.from_dict(data)  # ty: ignore[invalid-attribute-access]
    return profile
