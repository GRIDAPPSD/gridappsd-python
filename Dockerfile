# GridAPPS-D Python Client Base Image
#
# This image provides a ready-to-use environment with gridappsd-python installed.
# Use it as a base for your GridAPPS-D client applications.
#
# NOTE: This is NOT the GridAPPS-D platform itself. To run the full platform,
# use gridappsd-docker: https://github.com/GRIDAPPSD/gridappsd-docker
#
# Available tags:
#   - gridappsd/gridappsd-python:latest          (Python 3.12, latest stable release)
#   - gridappsd/gridappsd-python:develop         (Python 3.12, latest dev release)
#   - gridappsd/gridappsd-python:<version>       (Python 3.12, specific version)
#   - gridappsd/gridappsd-python:<version>-py310 (Python 3.10, specific version)
#   - gridappsd/gridappsd-python:<version>-py311 (Python 3.11, specific version)
#   - gridappsd/gridappsd-python:<version>-py312 (Python 3.12, specific version)
#
# Usage - Create a client application:
#
#   FROM gridappsd/gridappsd-python:latest
#   COPY requirements.txt /app/
#   RUN pip install -r /app/requirements.txt
#   COPY my_app.py /app/
#   CMD ["python", "/app/my_app.py"]
#
# Build and run with GridAPPS-D platform:
#
#   # Build your app
#   docker build -t my-gridappsd-app .
#
#   # Run alongside GridAPPS-D (assumes gridappsd-docker is running)
#   docker run --rm --network gridappsd-docker_default \
#     -e GRIDAPPSD_ADDRESS=gridappsd \
#     my-gridappsd-app

ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

ARG GRIDAPPSD_PYTHON_VERSION

# Python environment settings
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# GridAPPS-D connection defaults (override at runtime)
ENV GRIDAPPSD_ADDRESS="gridappsd" \
    GRIDAPPSD_PORT="61613" \
    GRIDAPPSD_USER="app_user" \
    GRIDAPPSD_PASSWORD="1234App"

# Install system dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install gridappsd-python
# If GRIDAPPSD_PYTHON_VERSION is set (e.g., "==2025.3.2"), use it
# Otherwise install latest from PyPI
# --pre allows installing prerelease versions (e.g., 2025.3.2a15)
RUN pip install --upgrade pip \
    && pip install --pre gridappsd-python${GRIDAPPSD_PYTHON_VERSION:-}

# Default command shows installed version
CMD ["python", "-c", "import gridappsd; print(f'gridappsd-python version: {gridappsd.__version__}')"]
