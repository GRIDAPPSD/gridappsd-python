# Docker Environment for Applications

The `gridappsd/gridappsd-python` Docker image provides a Python environment with `gridappsd-python` pre-installed. Use it as a base for building GridAPPS-D client applications.

**Important:** This is NOT the GridAPPS-D platform. To run the platform, use [gridappsd-docker](https://github.com/GRIDAPPSD/gridappsd-docker).

## Available Tags

| Tag | Python | Description |
|-----|--------|-------------|
| `latest` | 3.12 | Latest stable release |
| `develop` | 3.12 | Latest development release |
| `<version>` | 3.12 | Specific version (e.g., `2025.4.0`) |
| `<version>-py310` | 3.10 | Specific version with Python 3.10 |
| `<version>-py311` | 3.11 | Specific version with Python 3.11 |
| `<version>-py312` | 3.12 | Specific version with Python 3.12 |

## Building a Client Application

### Basic Dockerfile

```dockerfile
FROM gridappsd/gridappsd-python:latest

WORKDIR /app

# Install additional dependencies (optional)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY my_app.py ./

CMD ["python", "my_app.py"]
```

### Build and Run

```shell
# Build your application image
docker build -t my-gridappsd-app .

# Run alongside GridAPPS-D platform
# (assumes gridappsd-docker is running)
docker run --rm \
  --network gridappsd-docker_default \
  -e GRIDAPPSD_ADDRESS=gridappsd \
  -e GRIDAPPSD_PORT=61613 \
  -e GRIDAPPSD_USER=app_user \
  -e GRIDAPPSD_PASSWORD=1234App \
  my-gridappsd-app
```

## Environment Variables

The image sets these defaults (override at runtime):

| Variable | Default | Description |
|----------|---------|-------------|
| `GRIDAPPSD_ADDRESS` | `gridappsd` | Hostname of GridAPPS-D server |
| `GRIDAPPSD_PORT` | `61613` | STOMP port |
| `GRIDAPPSD_USER` | `app_user` | Username |
| `GRIDAPPSD_PASSWORD` | `1234App` | Password |

## Running with GridAPPS-D Platform

### Option 1: Using pixi tasks

```shell
# Start the GridAPPS-D platform
pixi run docker-up

# Run your app
docker run --rm --network gridappsd-docker_default my-gridappsd-app

# Stop the platform when done
pixi run docker-down
```

### Option 2: Using docker-compose

Add your application to a `docker-compose.yml`:

```yaml
version: '3'

services:
  my-app:
    build: .
    depends_on:
      - gridappsd
    environment:
      - GRIDAPPSD_ADDRESS=gridappsd
    networks:
      - gridappsd-docker_default

networks:
  gridappsd-docker_default:
    external: true
```

## Example Application

See [gridappsd-sample-app](https://github.com/GRIDAPPSD/gridappsd-sample-app) for a complete example.

### Minimal Example

```python
# my_app.py
from gridappsd import GridAPPSD

def on_message(header, message):
    print(f"Received: {message}")

# Connect using environment variables
gapps = GridAPPSD()
assert gapps.connected, "Failed to connect to GridAPPS-D"

print(f"Connected to GridAPPS-D")

# Subscribe to simulation output
gapps.subscribe('/topic/goss.gridappsd.simulation.output.>', on_message)

# Keep running
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    gapps.close()
```

## Choosing a Python Version

If your application requires a specific Python version:

```dockerfile
# Use Python 3.10 for compatibility with older dependencies
FROM gridappsd/gridappsd-python:2025.4.0-py310

# ... rest of Dockerfile
```
