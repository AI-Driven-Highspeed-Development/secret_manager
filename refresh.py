"""Refresh script for secret_manager.

Registers CLI commands with CLIManager.

Run via: python adhd_framework.py refresh --module secret-manager
"""

from __future__ import annotations

from logger_util import Logger


def main() -> None:
    """Refresh secret_manager — register CLI commands."""
    logger = Logger(name="secret_managerRefresh")

    from secret_manager.secret_cli import register_cli

    register_cli()
    logger.info("secret_manager refresh complete (CLI commands registered)")
