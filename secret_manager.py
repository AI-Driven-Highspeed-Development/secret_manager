from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Any, Optional

import yaml

from exceptions_core import ADHDError
from logger_util import Logger


class SecretNotIgnoredError(ADHDError):
    """Raised when attempting to write secrets that aren't gitignored."""
    pass


class SecretManager:
    """Manage API keys and sensitive configuration securely.

    Stores secrets in a YAML file and ensures the secrets file is
    NEVER pushed to git by managing .gitignore entries.

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
            True if secrets file path matches a pattern in .gitignore.
        """
        project_root = self._find_project_root()
        gitignore_path = project_root / ".gitignore"
        if not gitignore_path.exists():
            return False
        content = gitignore_path.read_text(encoding="utf-8")
        try:
            rel = str(self.secrets_path.relative_to(project_root))
        except ValueError:
            rel = self.secrets_path.name
        return self._pattern_in_gitignore(content, rel)

    # ---------------- Internal helpers ----------------

    @staticmethod
    def _pattern_in_gitignore(content: str, pattern: str) -> bool:
        """Check if a pattern (or its parent glob) appears in gitignore content."""
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Exact match or fnmatch-style match
            if line == pattern or line == pattern.split("/")[-1]:
                return True
            # Glob match (e.g. "secrets.*.yaml" matches "secrets.prod.yaml")
            if fnmatch.fnmatch(pattern, line) or fnmatch.fnmatch(pattern.split("/")[-1], line):
                return True
        return False

    def _find_project_root(self) -> Path:
        """Find the project root by looking for pyproject.toml or .git."""
        current = Path.cwd()

        for parent in [current] + list(current.parents):
            if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
                return parent

        return current

    def _ensure_secrets_ignored(self) -> None:
        """Ensure all secrets patterns are in .gitignore."""
        project_root = self._find_project_root()
        gitignore_path = project_root / ".gitignore"

        # Read existing content
        existing = ""
        if gitignore_path.exists():
            existing = gitignore_path.read_text(encoding="utf-8")

        patterns_to_add: list[str] = []
        for pattern in self.SECRETS_PATTERNS:
            if not self._pattern_in_gitignore(existing, pattern):
                patterns_to_add.append(pattern)

        if patterns_to_add:
            lines = existing.rstrip("\n")
            section = "\n# Secrets (managed by secret_manager)\n"
            section += "\n".join(patterns_to_add) + "\n"
            gitignore_path.write_text(
                lines + "\n" + section if lines else section,
                encoding="utf-8",
            )
            self.logger.debug("Secrets patterns added to .gitignore")

    def _validate_ignored_before_write(self) -> None:
        """Validate that secrets file is ignored before any write operation."""
        project_root = self._find_project_root()
        gitignore_path = project_root / ".gitignore"

        if not gitignore_path.exists():
            raise SecretNotIgnoredError(
                f"SECURITY: No .gitignore found at '{project_root}'. "
                f"Refusing to write secrets. Ensure a .gitignore exists."
            )

        content = gitignore_path.read_text(encoding="utf-8")

        # Check if any of our patterns are covered
        for pattern in self.SECRETS_PATTERNS:
            if self._pattern_in_gitignore(content, pattern):
                return

        # Also check the secrets filename itself
        if self._pattern_in_gitignore(content, self.secrets_path.name):
            return

        # Check relative path
        try:
            rel = str(self.secrets_path.relative_to(project_root))
            if self._pattern_in_gitignore(content, rel):
                return
        except ValueError:
            pass

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

        # Restrict permissions to owner only (0600)
        os.chmod(self.secrets_path, 0o600)
