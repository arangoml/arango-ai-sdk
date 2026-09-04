"""Secret profile namespace.

A secret profile holds one secret (an API key) that the platform stores
encrypted. Later stages reference a profile by its ID instead of sending the
key itself: AutoGraph takes one profile ID for the chat model and one for the
embedding model. The user never sees an endpoint, a header, or a token here.
"""

from collections.abc import Mapping
from typing import Any

from arango_platform_clients.secrets import Profile, ProfileType

from arango_ai_sdk.communication import Communication

__all__ = ["SecretProfileManager"]

# ACP service sits behind this prefix on the gateway. The proto paths are
# relative to it, so `post: "/v1/secrets"` is reached at "/ai/v1/secrets".
_SECRETS_PATH = "/ai/v1/secrets"


class SecretProfileManager:
    """Create and fetch secret profiles through the communication layer.

    Parameters
    ----------
    communication : Communication
        Shared transport. This namespace calls ``send_request`` and nothing else.
    """

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
        raise NotImplementedError

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
        raise NotImplementedError


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
    raise NotImplementedError
