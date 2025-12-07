from __future__ import annotations

from pathlib import Path
from typing import Any, Optional


import yaml

from cores.exceptions_core.adhd_exceptions import ADHDError
from managers.ignore_manager import IgnoreManager
from utils.logger_util import Logger


class SecretNotIgnoredError(ADHDError):
    """Raised when attempting to write secrets that aren't gitignored."""
    pass


class SecretManager:
    """Manage API keys and sensitive configuration securely.

    Stores secrets in a YAML file and uses IgnoreManager to GUARANTEE
    the secrets file is NEVER pushed to git.

    Default location: project/data/secrets.yaml
    """

    DEFAULT_SECRETS_PATH = "project/data/secrets.yaml"
    SECRETS_PATTERNS = [
        "project/data/secrets.yaml",
        "project/data/secrets.*.yaml",
    ]

    def __init__(
        self,
        secrets_path: Optional[str] = None,
        auto_ensure_ignored: bool = True
    ) -> None:
        """Initialize SecretManager.

        Args:
            secrets_path: Custom path to secrets file. Defaults to project/data/secrets.yaml.
            auto_ensure_ignored: If True, automatically add secrets to .gitignore on init.
        """
        self.logger = Logger(name=__class__.__name__)
        self._ignore_manager = IgnoreManager()

        # Resolve secrets path
        if secrets_path:
            self.secrets_path = Path(secrets_path)
        else:
            self.secrets_path = self._find_project_root() / self.DEFAULT_SECRETS_PATH

        # Ensure secrets are ignored on init
        if auto_ensure_ignored:
            self._ensure_secrets_ignored()

    # ---------------- Public API ----------------

    def get_secret(self, key: str, default: Any = None) -> Any:
        """Get a secret value by key.

        Args:
            key: The secret key to retrieve.
            default: Value to return if key not found.

        Returns:
            The secret value, or default if not found.
        """
        secrets = self._load_secrets()
        return secrets.get(key, default)

    def set_secret(self, key: str, value: Any) -> None:
        """Set a secret value.

        Args:
            key: The secret key.
            value: The secret value to store.

        Raises:
            SecretNotIgnoredError: If secrets file is not gitignored.
        """
        self._validate_ignored_before_write()

        secrets = self._load_secrets()
        secrets[key] = value
        self._save_secrets(secrets)
        self.logger.info(f"Secret '{key}' saved")

    def delete_secret(self, key: str) -> bool:
        """Delete a secret by key.

        Args:
            key: The secret key to delete.

        Returns:
            True if deleted, False if key didn't exist.

        Raises:
            SecretNotIgnoredError: If secrets file is not gitignored.
        """
        self._validate_ignored_before_write()

        secrets = self._load_secrets()
        if key not in secrets:
            self.logger.debug(f"Secret '{key}' not found")
            return False

        del secrets[key]
        self._save_secrets(secrets)
        self.logger.info(f"Secret '{key}' deleted")
        return True

    def list_secrets(self) -> list[str]:
        """List all secret keys (not values).

        Returns:
            List of secret key names.
        """
        secrets = self._load_secrets()
        return list(secrets.keys())

    def has_secret(self, key: str) -> bool:
        """Check if a secret exists.

        Args:
            key: The secret key to check.

        Returns:
            True if the secret exists.
        """
        secrets = self._load_secrets()
        return key in secrets

    def get_multiple(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple secrets at once.

        Args:
            keys: List of secret keys to retrieve.

        Returns:
            Dict mapping keys to values (missing keys have None values).
        """
        secrets = self._load_secrets()
        return {key: secrets.get(key) for key in keys}

    def is_protected(self) -> bool:
        """Check if secrets file is properly gitignored.

        Returns:
            True if secrets file is in the gitignore managed zone.
        """
        return self._ignore_manager.is_ignored(str(self.secrets_path.relative_to(self._find_project_root())))

    # ---------------- Internal helpers ----------------

    def _find_project_root(self) -> Path:
        """Find the project root by looking for init.yaml or .git."""
        current = Path.cwd()

        for parent in [current] + list(current.parents):
            if (parent / "init.yaml").exists() or (parent / ".git").exists():
                return parent

        return current

    def _ensure_secrets_ignored(self) -> None:
        """Ensure all secrets patterns are in .gitignore."""
        for pattern in self.SECRETS_PATTERNS:
            self._ignore_manager.ensure_ignored(pattern)
        self.logger.debug("Secrets patterns added to .gitignore managed zone")

    def _validate_ignored_before_write(self) -> None:
        """Validate that secrets file is ignored before any write operation."""
        # Check if any of our patterns are in the managed zone
        for pattern in self.SECRETS_PATTERNS:
            if self._ignore_manager.is_ignored(pattern):
                return  # At least one pattern is ignored, we're safe

        # Also check if the secrets filename itself is ignored
        if self._ignore_manager.is_ignored(self.secrets_path.name):
            return

        # Try to check relative path if within project root
        try:
            project_root = self._find_project_root()
            relative_path = str(self.secrets_path.relative_to(project_root))
            if self._ignore_manager.is_globally_ignored(relative_path):
                return
        except ValueError:
            # secrets_path is not under project root (e.g., temp directory)
            # Check if just the filename is globally ignored
            if self._ignore_manager.is_globally_ignored(self.secrets_path.name):
                return

        raise SecretNotIgnoredError(
            f"SECURITY: Secrets file '{self.secrets_path}' is NOT in .gitignore! "
            f"Refusing to write secrets. Call ensure_ignored() first or add manually."
        )

    def _ensure_parent_dir(self) -> None:
        """Ensure the parent directory exists."""
        self.secrets_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_secrets(self) -> dict[str, Any]:
        """Load secrets from YAML file."""
        if not self.secrets_path.exists():
            return {}

        try:
            content = self.secrets_path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
            return data if isinstance(data, dict) else {}
        except yaml.YAMLError as e:
            self.logger.error(f"Failed to parse secrets file: {e}")
            return {}

    def _save_secrets(self, secrets: dict[str, Any]) -> None:
        """Save secrets to YAML file."""
        self._ensure_parent_dir()

        content = yaml.dump(secrets, default_flow_style=False, allow_unicode=True)
        self.secrets_path.write_text(content, encoding="utf-8")
