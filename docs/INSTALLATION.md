# Installation Guide

This guide covers different ways to add `gridappsd-python` as a dependency in your project.

## Quick Install

```shell
pip install gridappsd-python
```

## Adding as a Dependency

### requirements.txt

```txt
# Stable release from PyPI
gridappsd-python>=2025.3.0

# Or pin to a specific version
gridappsd-python==2025.3.2

# Development release from GitHub
gridappsd-python @ https://github.com/GRIDAPPSD/gridappsd-python/releases/download/v2025.3.2a14/gridappsd_python-2025.3.2a14-py3-none-any.whl

# Or install from a git tag
gridappsd-python @ git+https://github.com/GRIDAPPSD/gridappsd-python.git@v2025.3.2a14#subdirectory=gridappsd-python-lib

# Or install from the develop branch (latest development code)
gridappsd-python @ git+https://github.com/GRIDAPPSD/gridappsd-python.git@develop#subdirectory=gridappsd-python-lib
```

### pyproject.toml (PEP 621 / pip)

```toml
[project]
dependencies = [
    # Stable release from PyPI
    "gridappsd-python>=2025.3.0",
]

# For development releases, use optional dependencies
[project.optional-dependencies]
dev = [
    "gridappsd-python @ git+https://github.com/GRIDAPPSD/gridappsd-python.git@develop#subdirectory=gridappsd-python-lib",
]
```

### pyproject.toml (Poetry)

```toml
[tool.poetry.dependencies]
# Stable release from PyPI
gridappsd-python = "^2025.3.0"

# Or pin to specific version
gridappsd-python = "2025.3.2"

# Development release from git
gridappsd-python = { git = "https://github.com/GRIDAPPSD/gridappsd-python.git", branch = "develop", subdirectory = "gridappsd-python-lib" }

# Or from a specific tag
gridappsd-python = { git = "https://github.com/GRIDAPPSD/gridappsd-python.git", tag = "v2025.3.2a14", subdirectory = "gridappsd-python-lib" }
```

### pixi.toml

```toml
[pypi-dependencies]
# Stable release from PyPI
gridappsd-python = ">=2025.3.0"

# Or pin to specific version
gridappsd-python = "==2025.3.2"

# Development release from git
gridappsd-python = { git = "https://github.com/GRIDAPPSD/gridappsd-python.git", branch = "develop", subdirectory = "gridappsd-python-lib" }

# Or from a specific tag
gridappsd-python = { git = "https://github.com/GRIDAPPSD/gridappsd-python.git", tag = "v2025.3.2a14", subdirectory = "gridappsd-python-lib" }

# Or from a specific commit
gridappsd-python = { git = "https://github.com/GRIDAPPSD/gridappsd-python.git", rev = "abc1234", subdirectory = "gridappsd-python-lib" }
```

## Including gridappsd-field-bus

The `gridappsd-field-bus` package provides additional field bus functionality and depends on `gridappsd-python`.

### requirements.txt

```txt
# Both packages from PyPI
gridappsd-python>=2025.3.0
gridappsd-field-bus>=2025.3.0

# Or from GitHub releases
gridappsd-python @ https://github.com/GRIDAPPSD/gridappsd-python/releases/download/v2025.3.2a14/gridappsd_python-2025.3.2a14-py3-none-any.whl
gridappsd-field-bus @ https://github.com/GRIDAPPSD/gridappsd-python/releases/download/v2025.3.2a14/gridappsd_field_bus-2025.3.2a14-py3-none-any.whl
```

### pyproject.toml (PEP 621)

```toml
[project]
dependencies = [
    "gridappsd-python>=2025.3.0",
    "gridappsd-field-bus>=2025.3.0",
]
```

### pyproject.toml (Poetry)

```toml
[tool.poetry.dependencies]
gridappsd-python = "^2025.3.0"
gridappsd-field-bus = "^2025.3.0"

# Or from git (both packages)
gridappsd-python = { git = "https://github.com/GRIDAPPSD/gridappsd-python.git", branch = "develop", subdirectory = "gridappsd-python-lib" }
gridappsd-field-bus = { git = "https://github.com/GRIDAPPSD/gridappsd-python.git", branch = "develop", subdirectory = "gridappsd-field-bus-lib" }
```

### pixi.toml

```toml
[pypi-dependencies]
gridappsd-python = ">=2025.3.0"
gridappsd-field-bus = ">=2025.3.0"

# Or from git
gridappsd-python = { git = "https://github.com/GRIDAPPSD/gridappsd-python.git", branch = "develop", subdirectory = "gridappsd-python-lib" }
gridappsd-field-bus = { git = "https://github.com/GRIDAPPSD/gridappsd-python.git", branch = "develop", subdirectory = "gridappsd-field-bus-lib" }
```

## Version Specifiers

| Specifier | Meaning |
|-----------|---------|
| `>=2025.3.0` | Version 2025.3.0 or newer |
| `^2025.3.0` | Compatible with 2025.3.x (Poetry) |
| `~=2025.3.0` | Compatible release (>=2025.3.0, <2026.0.0) |
| `==2025.3.2` | Exact version |
| `>=2025.3.0,<2026.0.0` | Range |

## Verifying Installation

```python
import gridappsd
print(gridappsd.__version__)

# Test connection (requires running GridAPPS-D instance)
from gridappsd import GridAPPSD
gapps = GridAPPSD()
print(f"Connected: {gapps.connected}")
```

## Troubleshooting

### Git dependency not installing

If you get errors with git dependencies, ensure you have git installed and accessible:

```shell
git --version
```

### SSL certificate errors

If you encounter SSL errors when installing from GitHub, do **not** bypass certificate verification, as this can expose you to security risks.

Instead, try the following steps:

- Ensure your system's CA certificates are up to date. On Ubuntu/Debian, run:  
  ```shell
  sudo apt-get update && sudo apt-get install --reinstall ca-certificates
### Subdirectory not found

When using git dependencies with subdirectories, ensure the syntax is correct:

```shell
# Correct
pip install "git+https://github.com/GRIDAPPSD/gridappsd-python.git@develop#subdirectory=gridappsd-python-lib"

# Wrong (missing subdirectory)
pip install "git+https://github.com/GRIDAPPSD/gridappsd-python.git@develop"
```
