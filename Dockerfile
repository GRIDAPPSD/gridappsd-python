# GridAPPS-D Python Client Base Image
#
# This image provides a ready-to-use environment with gridappsd-python installed.
# Use it as a base for your GridAPPS-D applications.
#
# Usage:
#   FROM gridappsd/gridappsd-python:latest
#   COPY your_app.py /app/
#   CMD ["python", "/app/your_app.py"]

FROM python:3.12-slim as base

ARG GRIDAPPSD_PYTHON_VERSION

# Python environment settings
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# GridAPPS-D environment
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
RUN pip install --upgrade pip \
    && pip install gridappsd-python${GRIDAPPSD_PYTHON_VERSION:-}

# Default command shows installed version
CMD ["python", "-c", "import gridappsd; print(f'gridappsd-python version: {gridappsd.__version__}')"]
