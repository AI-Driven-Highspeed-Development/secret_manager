"""CLI commands and registration for secret_manager."""

import argparse
import getpass
import sys

from managers.secret_manager.secret_manager import SecretManager
from managers.cli_manager import CLIManager, ModuleRegistration, Command, CommandArg


# ─────────────────────────────────────────────────────────────────────────────
# Handler Functions
# ─────────────────────────────────────────────────────────────────────────────

def list_secrets(args: argparse.Namespace) -> int:
    """List all secret keys."""
    sm = SecretManager()
    keys = sm.list_secrets()
    if keys:
        print("Secrets:")
        for k in keys:
            print(f"  - {k}")
    else:
        print("No secrets found.")
    return 0


def get_secret(args: argparse.Namespace) -> int:
    """Get a secret value."""
    sm = SecretManager()
    val = sm.get_secret(args.key)
    if val is not None:
        print(val)
        return 0
    else:
        print(f"Secret '{args.key}' not found.", file=sys.stderr)
        return 1


def set_secret(args: argparse.Namespace) -> int:
    """Set a secret value."""
    sm = SecretManager()
    val = getpass.getpass(f"Enter value for '{args.key}': ")
    if not val:
        print("Aborted: Empty value.")
        return 1
    sm.set_secret(args.key, val)
    print(f"Secret '{args.key}' set successfully.")
    return 0


def delete_secret(args: argparse.Namespace) -> int:
    """Delete a secret."""
    sm = SecretManager()
    if sm.delete_secret(args.key):
        print(f"Secret '{args.key}' deleted.")
        return 0
    else:
        print(f"Secret '{args.key}' not found.", file=sys.stderr)
        return 1


# ─────────────────────────────────────────────────────────────────────────────
# CLI Registration
# ─────────────────────────────────────────────────────────────────────────────

def register_cli() -> None:
    """Register secret_manager commands with CLIManager."""
    cli = CLIManager()
    cli.register_module(ModuleRegistration(
        module_name="secret_manager",
        short_name="sm",
        description="Manage secrets securely",
        commands=[
            Command(
                name="list",
                help="List all secret keys",
                handler="managers.secret_manager.secret_cli:list_secrets",
            ),
            Command(
                name="get",
                help="Get a secret value",
                handler="managers.secret_manager.secret_cli:get_secret",
                args=[
                    CommandArg(name="key", help="The secret key"),
                ],
            ),
            Command(
                name="set",
                help="Set a secret value",
                handler="managers.secret_manager.secret_cli:set_secret",
                args=[
                    CommandArg(name="key", help="The secret key"),
                ],
            ),
            Command(
                name="delete",
                help="Delete a secret",
                handler="managers.secret_manager.secret_cli:delete_secret",
                args=[
                    CommandArg(name="key", help="The secret key"),
                ],
            ),
        ],
    ))

