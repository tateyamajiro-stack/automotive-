"""Encrypted connection configuration for Jira / Confluence Data Center."""

from __future__ import annotations

import base64
import getpass
import hashlib
import socket
from typing import TYPE_CHECKING

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

if TYPE_CHECKING:
    from hils_manager.repositories.settings_repo import SettingsRepository

# Settings keys ----------------------------------------------------------

_JIRA_BASE_URL = "jira.base_url"
_JIRA_PAT_ENC = "jira.pat_encrypted"
_JIRA_DEFAULT_PROJECT_KEY = "jira.default_project_key"

_CONFLUENCE_BASE_URL = "confluence.base_url"
_CONFLUENCE_PAT_ENC = "confluence.pat_encrypted"
_CONFLUENCE_SPACE_KEY = "confluence.space_key"
_CONFLUENCE_PARENT_PAGE_ID = "confluence.parent_page_id"


class ConnectionConfig:
    """Manage encrypted PAT storage for Jira and Confluence.

    PATs are encrypted at rest using :class:`~cryptography.fernet.Fernet`
    with a key derived from a machine-specific salt (hostname + username)
    via PBKDF2-HMAC-SHA256.

    All values are persisted in the ``app_settings`` table through
    :class:`SettingsRepository`.
    """

    _KDF_ITERATIONS = 480_000

    def __init__(self, settings_repo: SettingsRepository) -> None:
        self._repo = settings_repo
        self._fernet = self._build_fernet()

    # ------------------------------------------------------------------
    # Key derivation
    # ------------------------------------------------------------------

    @staticmethod
    def _machine_salt() -> bytes:
        """Derive a reproducible salt from the current machine identity."""
        identity = f"{socket.gethostname()}:{getpass.getuser()}"
        return hashlib.sha256(identity.encode()).digest()

    @classmethod
    def _build_fernet(cls) -> Fernet:
        """Create a :class:`Fernet` instance from the machine-specific key."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=cls._machine_salt(),
            iterations=cls._KDF_ITERATIONS,
        )
        # A fixed passphrase combined with the machine salt keeps the key
        # deterministic on the same host/user while preventing trivial
        # copy-paste of encrypted tokens to other machines.
        key = base64.urlsafe_b64encode(kdf.derive(b"hils-manager-pat"))
        return Fernet(key)

    # ------------------------------------------------------------------
    # Encryption helpers
    # ------------------------------------------------------------------

    def _encrypt(self, plaintext: str) -> str:
        """Encrypt *plaintext* and return a base-64 encoded token."""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def _decrypt(self, ciphertext: str) -> str:
        """Decrypt a base-64 encoded *ciphertext* token."""
        return self._fernet.decrypt(ciphertext.encode()).decode()

    # ------------------------------------------------------------------
    # Jira configuration
    # ------------------------------------------------------------------

    def get_jira_config(self) -> dict[str, str] | None:
        """Return Jira connection details, or ``None`` if not configured.

        The returned dict contains ``base_url`` and ``pat``.
        """
        base_url = self._repo.get(_JIRA_BASE_URL)
        pat_enc = self._repo.get(_JIRA_PAT_ENC)
        if not base_url or not pat_enc:
            return None
        return {
            "base_url": base_url,
            "pat": self._decrypt(pat_enc),
            "default_project_key": self._repo.get(_JIRA_DEFAULT_PROJECT_KEY) or "",
        }

    def set_jira_config(
        self, base_url: str, pat: str, default_project_key: str = ""
    ) -> None:
        """Persist Jira connection details.

        The PAT is encrypted before storage.
        """
        self._repo.set(_JIRA_BASE_URL, base_url, "Jira Data Center base URL")
        self._repo.set(
            _JIRA_PAT_ENC,
            self._encrypt(pat),
            "Jira Personal Access Token (encrypted)",
        )
        self._repo.set(
            _JIRA_DEFAULT_PROJECT_KEY,
            default_project_key,
            "Jira default project key",
        )

    def is_jira_configured(self) -> bool:
        """Return ``True`` if Jira credentials are stored."""
        return (
            self._repo.get(_JIRA_BASE_URL) is not None
            and self._repo.get(_JIRA_PAT_ENC) is not None
        )

    def clear_jira_config(self) -> None:
        """Remove all stored Jira credentials."""
        self._repo.delete(_JIRA_BASE_URL)
        self._repo.delete(_JIRA_PAT_ENC)
        self._repo.delete(_JIRA_DEFAULT_PROJECT_KEY)

    # ------------------------------------------------------------------
    # Confluence configuration
    # ------------------------------------------------------------------

    def get_confluence_config(self) -> dict[str, str] | None:
        """Return Confluence connection details, or ``None`` if not configured.

        The returned dict contains ``base_url``, ``pat``, ``space_key``,
        and ``parent_page_id``.
        """
        base_url = self._repo.get(_CONFLUENCE_BASE_URL)
        pat_enc = self._repo.get(_CONFLUENCE_PAT_ENC)
        space_key = self._repo.get(_CONFLUENCE_SPACE_KEY)
        parent_page_id = self._repo.get(_CONFLUENCE_PARENT_PAGE_ID)
        if not base_url or not pat_enc:
            return None
        return {
            "base_url": base_url,
            "pat": self._decrypt(pat_enc),
            "space_key": space_key or "",
            "parent_page_id": parent_page_id or "",
        }

    def set_confluence_config(
        self,
        base_url: str,
        pat: str,
        space_key: str,
        parent_page_id: str,
    ) -> None:
        """Persist Confluence connection details.

        The PAT is encrypted before storage.
        """
        self._repo.set(
            _CONFLUENCE_BASE_URL, base_url, "Confluence Data Center base URL"
        )
        self._repo.set(
            _CONFLUENCE_PAT_ENC,
            self._encrypt(pat),
            "Confluence Personal Access Token (encrypted)",
        )
        self._repo.set(
            _CONFLUENCE_SPACE_KEY, space_key, "Confluence space key"
        )
        self._repo.set(
            _CONFLUENCE_PARENT_PAGE_ID,
            parent_page_id,
            "Confluence parent page ID for generated pages",
        )

    def is_confluence_configured(self) -> bool:
        """Return ``True`` if Confluence credentials are stored."""
        return (
            self._repo.get(_CONFLUENCE_BASE_URL) is not None
            and self._repo.get(_CONFLUENCE_PAT_ENC) is not None
        )

    def clear_confluence_config(self) -> None:
        """Remove all stored Confluence credentials."""
        self._repo.delete(_CONFLUENCE_BASE_URL)
        self._repo.delete(_CONFLUENCE_PAT_ENC)
        self._repo.delete(_CONFLUENCE_SPACE_KEY)
        self._repo.delete(_CONFLUENCE_PARENT_PAGE_ID)
