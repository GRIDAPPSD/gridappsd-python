## Use latest slim Python image. Note that it's built on Debian Stretch.
# `python-base` sets up all our shared environment variables
FROM python:3.14.0rc2-slim as python-base

ARG GRIDAPPSD_PYTHON_VERSION

    # python
ENV PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # paths
    # this is where our requirements + virtual environment will live
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"


# prepend poetry and venv to path
ENV PATH="$VENV_PATH/bin:$PATH"

# gridappsd environment
ENV GRIDAPPSD_PORT="61613" \
    GRIDAPPSD_URI="tcp://gridappsd:${GRIDAPPSD_PORT}" \
    GRIDAPPSD_USER="app_user" \
    GRIDAPPSD_PASSWORD="1234App" \
    GRIDAPPSD_PYTHON_VERSION=${GRIDAPPSD_PYTHON_VERSION}


# `builder-base` stage is used to build deps + create our virtual environment
FROM python-base as builder-base
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        # deps for installing poetry
        curl \
        # deps for building python deps
        build-essential

# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH

RUN python -m "venv" "$VENV_PATH" \
    && "$VENV_PATH/bin/pip3" install --upgrade gridappsd-python${GRIDAPPSD_PYTHON_VERSION}

# `development` image is used during development / testing
FROM python-base as development
ENV GRIDAPPSD_ENV=production
WORKDIR $PYSETUP_PATH

# # copy in our built poetry + venv
# COPY --from=builder-base $POETRY_HOME $POETRY_HOME
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

# quicker install as runtime deps are already installed
# RUN poetry install

# # will become mountpoint of our code
# WORKDIR /code

# # `production` image used for runtime
# FROM python-base as production
# ENV GRIDAPPSD_ENV=production
# COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH
# COPY . /code
# WORKDIR /code
CMD ["register_app"]
