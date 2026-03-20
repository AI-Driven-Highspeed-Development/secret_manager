"""secret_manager — Secure API key and sensitive configuration management."""

from secret_manager.secret_manager import SecretManager, SecretNotIgnoredError

__all__ = ["SecretManager", "SecretNotIgnoredError"]
