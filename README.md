# Secret Manager

## Overview

Securely manage API keys and sensitive configuration. Stores secrets in `project/data/secrets.yaml` and uses `IgnoreManager` to **GUARANTEE** the secrets file is NEVER pushed to git.

## Security Features

- **Auto-gitignore**: On initialization, automatically adds secrets patterns to `.gitignore`
- **Write validation**: Refuses to write if secrets file isn't gitignored
- **Managed zone**: Uses `IgnoreManager`'s private zone for reliable protection
- **Pattern coverage**: Protects both `secrets.yaml` and `secrets.*.yaml` variants

## Usage

```python
from managers.secret_manager import SecretManager

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
from managers.secret_manager import SecretManager, SecretNotIgnoredError

try:
    secrets.set_secret("KEY", "value")
except SecretNotIgnoredError:
    print("DANGER: Secrets file is not gitignored!")
```

## Module Structure

```
managers/secret_manager/
├── __init__.py          # Module exports
├── init.yaml            # Module metadata
├── secret_manager.py    # SecretManager class
└── README.md            # This file
```

## Dependencies

- `ignore_manager` - For gitignore protection
- `logger_util` - For logging
- `exceptions_core` - For ADHDError base class
- `PyYAML` - For secrets file parsing
