"""Refresh script for secret_manager."""

import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = Path.cwd()

sys.path.insert(0, str(PROJECT_ROOT))

from managers.secret_manager.secret_cli import register_cli


def refresh() -> None:
    """Register CLI commands for secret_manager."""
    register_cli()


if __name__ == "__main__":
    refresh()
