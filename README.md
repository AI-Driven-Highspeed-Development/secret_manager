# Secret Manager

## Overview

Securely manage API keys and sensitive configuration. Stores secrets in `project/data/secrets.yaml` and ensures the secrets file is NEVER pushed to git via `.gitignore` management.

## Security Features

- **Auto-gitignore**: On initialization, automatically adds secrets patterns to `.gitignore`
- **Write validation**: Refuses to write if secrets file isn't gitignored
- **Pattern coverage**: Protects both `secrets.yaml` and `secrets.*.yaml` variants

## CLI Usage

```bash
# List all secrets
python adhd_framework.py sm list

# Set a secret (securely prompts for input)
python adhd_framework.py sm set OPENAI_API_KEY

# Get a secret value
python adhd_framework.py sm get OPENAI_API_KEY

# Delete a secret
python adhd_framework.py sm delete OPENAI_API_KEY
```

## Usage

```python
from secret_manager import SecretManager

# Initialize (auto-adds to .gitignore)
secrets = SecretManager()

# Store a secret
secrets.set_secret("OPENAI_API_KEY", "sk-...")
secrets.set_secret("DATABASE_URL", "postgresql://...")

# Retrieve a secret
api_key = secrets.get_secret("OPENAI_API_KEY")
db_url = secrets.get_secret("DATABASE_URL", default="sqlite:///local.db")

# Check if secret exists
if secrets.has_secret("OPENAI_API_KEY"):
    print("API key configured!")

# List all secret keys (not values)
for key in secrets.list_secrets():
    print(f"Secret: {key}")

# Delete a secret
secrets.delete_secret("OLD_API_KEY")

# Get multiple secrets at once
creds = secrets.get_multiple(["API_KEY", "API_SECRET"])

# Check if properly protected
if secrets.is_protected():
    print("Secrets are gitignored!")
```

## Custom Secrets Path

```python
# Use a different secrets file
secrets = SecretManager(secrets_path="config/my_secrets.yaml")

# Disable auto-gitignore (not recommended)
secrets = SecretManager(auto_ensure_ignored=False)
```

## Error Handling

```python
from secret_manager import SecretManager, SecretNotIgnoredError

try:
    secrets.set_secret("KEY", "value")
except SecretNotIgnoredError:
    print("DANGER: Secrets file is not gitignored!")
```

## Module Structure

```
modules/foundation/secret_manager/
├── __init__.py          # Module exports
├── pyproject.toml       # Module metadata and dependencies
├── secret_manager.py    # SecretManager class
├── secret_cli.py        # CLI commands
├── refresh.py           # CLI registration on refresh
├── .config_template     # Config defaults
└── README.md            # This file
```

## Dependencies

- `logger_util` — Structured logging
- `exceptions_core` — `ADHDError` base class
- `cli_manager` — CLI command registration
- `PyYAML` — Secrets file parsing
