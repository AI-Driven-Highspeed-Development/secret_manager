#!/usr/bin/env python3
import argparse
import getpass
import os
import sys

# Add project root to path to allow absolute imports
# managers/secret_manager/secret_cli.py -> managers/secret_manager -> managers -> root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from managers.secret_manager.secret_manager import SecretManager

def main():
    parser = argparse.ArgumentParser(description="Manage secrets securely.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List
    subparsers.add_parser("list", help="List all secret keys")

    # Get
    get_parser = subparsers.add_parser("get", help="Get a secret value")
    get_parser.add_argument("key", help="The secret key")

    # Set
    set_parser = subparsers.add_parser("set", help="Set a secret value")
    set_parser.add_argument("key", help="The secret key")

    # Delete
    del_parser = subparsers.add_parser("delete", help="Delete a secret")
    del_parser.add_argument("key", help="The secret key")

    args = parser.parse_args()

    try:
        sm = SecretManager()

        if args.command == "list":
            keys = sm.list_secrets()
            if keys:
                print("Secrets:")
                for k in keys:
                    print(f"  - {k}")
            else:
                print("No secrets found.")

        elif args.command == "get":
            val = sm.get_secret(args.key)
            if val is not None:
                print(val)
            else:
                print(f"Secret '{args.key}' not found.", file=sys.stderr)
                sys.exit(1)

        elif args.command == "set":
            val = getpass.getpass(f"Enter value for '{args.key}': ")
            if not val:
                print("Aborted: Empty value.")
                sys.exit(1)
            sm.set_secret(args.key, val)
            print(f"Secret '{args.key}' set successfully.")

        elif args.command == "delete":
            if sm.delete_secret(args.key):
                print(f"Secret '{args.key}' deleted.")
            else:
                print(f"Secret '{args.key}' not found.", file=sys.stderr)
                sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
