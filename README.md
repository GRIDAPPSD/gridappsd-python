[![CI](https://github.com/GRIDAPPSD/gridappsd-python/actions/workflows/ci.yml/badge.svg)](https://github.com/GRIDAPPSD/gridappsd-python/actions/workflows/ci.yml)

# gridappsd-python

Python library for developing applications and services against the GridAPPS-D API.

## Requirements

- Python >= 3.10, < 4.0
- [Pixi](https://pixi.sh) (for development)

## Installation

### Stable Releases (PyPI)

Install the latest stable release from PyPI:

```shell
pip install gridappsd-python
```

### Development Releases (GitHub)

Development releases are published to GitHub Releases (not PyPI). To install a development version:

```shell
# Install a specific dev release directly from GitHub
pip install https://github.com/GRIDAPPSD/gridappsd-python/releases/download/v2025.3.2a14/gridappsd_python-2025.3.2a14-py3-none-any.whl

# Or install from a specific git tag
pip install git+https://github.com/GRIDAPPSD/gridappsd-python.git@v2025.3.2a14#subdirectory=gridappsd-python-lib

# Or install the latest from the develop branch
pip install git+https://github.com/GRIDAPPSD/gridappsd-python.git@develop#subdirectory=gridappsd-python-lib
```

Browse available releases at: https://github.com/GRIDAPPSD/gridappsd-python/releases

For detailed instructions on adding `gridappsd-python` to your project using `requirements.txt`, `pyproject.toml`, or `pixi.toml`, see the [Installation Guide](docs/INSTALLATION.md).

### For Developers

This project uses [Pixi](https://pixi.sh) for development environment and task management.

#### Install Pixi

```shell
curl -fsSL https://pixi.sh/install.sh | bash
```

#### Clone and Setup

```shell
git clone https://github.com/GRIDAPPSD/gridappsd-python -b develop
cd gridappsd-python

# Install all dependencies and create the development environment
pixi install

# Verify installation
pixi run test
```

#### Available Tasks

```shell
# List all available tasks
pixi task list

# Run tests
pixi run test              # Run main library tests
pixi run test-field-bus    # Run field bus tests
pixi run test-all          # Run all tests
pixi run test-cov          # Run tests with coverage

# Code quality
pixi run lint              # Run linter (ruff)
pixi run lint-fix          # Auto-fix lint issues
pixi run format            # Format code (ruff)
pixi run format-check      # Check formatting
pixi run typecheck         # Run type checker (mypy)
pixi run check             # Run all quality checks

# Building
pixi run build             # Build all packages
pixi run build-lib         # Build main library only
pixi run build-field-bus   # Build field bus library only

# CI workflows
pixi run ci                # Run full CI pipeline (lint + typecheck + tests)
pixi run release           # Full release workflow

# Docker (for integration testing)
pixi run docker-up         # Start GridAPPS-D containers
pixi run docker-down       # Stop containers
pixi run docker-logs       # Follow container logs

# Utilities
pixi run clean             # Clean build artifacts
pixi run pre-commit-install # Install pre-commit hooks
```

#### Testing with Different Python Versions

The project supports Python 3.10 through 3.14. You can run tests against specific versions:

```shell
pixi run -e py310 test     # Test with Python 3.10
pixi run -e py311 test     # Test with Python 3.11
pixi run -e py312 test     # Test with Python 3.12
pixi run -e py313 test     # Test with Python 3.13
pixi run -e py314 test     # Test with Python 3.14
```

## Quick Start

The following code snippet assumes you have a GridAPPS-D instance running using
[gridappsd-docker](https://github.com/GRIDAPPSD/gridappsd-docker).

```python
from gridappsd import GridAPPSD

def on_message_callback(header, message):
    print(f"header: {header} message: {message}")

# Note: credentials should be changed in a production environment!
username = "app_user"
password = "1234App"

# Connect to GridAPPS-D (defaults to localhost)
gapps = GridAPPSD(username=username, password=password)

assert gapps.connected

gapps.send('send.topic', {"foo": "bar"})

# Subscribe to a topic (pass the function, don't call it)
gapps.subscribe('subscribe.topic', on_message_callback)

gapps.send('subscribe.topic', 'A message about subscription')

import time
time.sleep(5)

gapps.close()
```

## Docker

### Running the GridAPPS-D Platform

The `docker-up` task clones and runs [gridappsd-docker](https://github.com/GRIDAPPSD/gridappsd-docker), which starts the **full GridAPPS-D platform** (including Blazegraph, MySQL, and all services):

```shell
# Start the full GridAPPS-D platform
pixi run docker-up

# View logs
pixi run docker-logs

# Stop the platform
pixi run docker-down
```

This is useful for integration testing your applications against a real GridAPPS-D instance.

### Client Application Base Image

We publish a **client base image** (`gridappsd/gridappsd-python`) for building containerized GridAPPS-D applications. This image is NOT the platform itself - it's a Python environment with `gridappsd-python` pre-installed.

**Available tags:**

| Tag | Description |
|-----|-------------|
| `latest` | Latest stable release (Python 3.12) |
| `develop` | Latest development release (Python 3.12) |
| `<version>` | Specific version (e.g., `2025.4.0`) |
| `<version>-py310` | Specific version with Python 3.10 |
| `<version>-py311` | Specific version with Python 3.11 |
| `<version>-py312` | Specific version with Python 3.12 |

**Example: Building a Client Application**

Create a `Dockerfile` for your application:

```dockerfile
FROM gridappsd/gridappsd-python:latest

# Install additional dependencies
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

# Copy your application
COPY my_app.py /app/

CMD ["python", "/app/my_app.py"]
```

Build and run alongside the GridAPPS-D platform:

```shell
# Build your app
docker build -t my-gridappsd-app .

# Start GridAPPS-D platform (if not already running)
pixi run docker-up

# Run your app on the same network
docker run --rm --network gridappsd-docker_default \
  -e GRIDAPPSD_ADDRESS=gridappsd \
  my-gridappsd-app
```

See also: [DOCKER_CONTAINER.md](DOCKER_CONTAINER.md) for more details.

## Application Developers

### Local Development

When developing applications locally (outside of Docker), set these environment variables:

```shell
# Address where the GridAPPS-D server is running (default: localhost)
export GRIDAPPSD_ADDRESS=localhost

# STOMP client port (default: 61613)
export GRIDAPPSD_PORT=61613

# Credentials
export GRIDAPPSD_USER=app_user
export GRIDAPPSD_PASSWORD=1234App
```

With environment variables set, you can connect without explicit credentials:

```python
from gridappsd import GridAPPSD

def on_message_callback(header, message):
    print(f"header: {header} message: {message}")

# Connect using environment variables
gapps = GridAPPSD()

assert gapps.connected

gapps.send('send.topic', {"foo": "bar"})
gapps.subscribe('subscribe.topic', on_message_callback)
gapps.send('subscribe.topic', 'A message about subscription')

import time
time.sleep(5)

gapps.close()
```

## Testing

### Running Tests

```shell
# Run all tests
pixi run test-all

# Run with coverage
pixi run test-cov
```

### Environment Variables for Testing

```shell
# Docker image tag to use (default: develop)
export GRIDAPPSD_TAG_ENV=develop

# Credentials for integration tests
export GRIDAPPSD_USER=system
export GRIDAPPSD_PASSWORD=manager
```

**Note:** The first test run will download Docker images from [GOSS-GridAPPS-D](http://github.com/GRIDAPPSD/GOSS-GridAPPS-D). This may take some time.

### Using Test Fixtures in Your Project

The `gridappsd-python` library provides testing fixtures through `gridappsd.docker_handler`. Create a `conftest.py` in your test directory:

```python
# conftest.py
import logging
import os
import sys

import pytest
from gridappsd import GridAPPSD, GOSS
from gridappsd.docker_handler import run_dependency_containers, run_gridappsd_container

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
logging.basicConfig(
    stream=sys.stdout,
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s|%(levelname)s|%(name)s|%(message)s"
)

STOP_CONTAINER_AFTER_TEST = os.environ.get('GRIDAPPSD_STOP_CONTAINERS_AFTER_TESTS', True)


@pytest.fixture(scope="module")
def docker_dependencies():
    with run_dependency_containers(stop_after=STOP_CONTAINER_AFTER_TEST) as dep:
        yield dep


@pytest.fixture
def gridappsd_client(request, docker_dependencies):
    with run_gridappsd_container(stop_after=STOP_CONTAINER_AFTER_TEST):
        gappsd = GridAPPSD()
        gappsd.connect()
        assert gappsd.connected

        if request.cls is not None:
            request.cls.gridappsd_client = gappsd
        yield gappsd

        gappsd.disconnect()


@pytest.fixture
def goss_client(docker_dependencies):
    with run_gridappsd_container(stop_after=STOP_CONTAINER_AFTER_TEST):
        goss = GOSS()
        goss.connect()
        assert goss.connected
        yield goss
```

Example test using the fixtures:

```python
import os
from unittest import mock
from gridappsd import ProcessStatusEnum

@mock.patch.dict(os.environ, {"GRIDAPPSD_APPLICATION_ID": "my_app.py"})
def test_gridappsd_status(gridappsd_client):
    gappsd = gridappsd_client
    assert "my_app.py" == gappsd.get_application_id()
    assert gappsd.get_application_status() == ProcessStatusEnum.STARTING.value

    gappsd.set_application_status("RUNNING")
    assert gappsd.get_application_status() == ProcessStatusEnum.RUNNING.value
```

## Project Structure

```
gridappsd-python/
├── gridappsd-python-lib/     # Main library
│   ├── gridappsd/            # Source code
│   └── tests/                # Tests
├── gridappsd-field-bus-lib/  # Field bus library
│   ├── gridappsd_field_bus/  # Source code
│   └── tests/                # Tests
├── pixi.toml                 # Pixi configuration
├── pixi.lock                 # Lock file
└── .github/workflows/        # CI workflows
```

## License

BSD-3-Clause
