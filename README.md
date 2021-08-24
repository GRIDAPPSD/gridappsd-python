[![Run All Pytests](https://github.com/GRIDAPPSD/gridappsd-python/actions/workflows/run-pytest.yml/badge.svg)](https://github.com/GRIDAPPSD/gridappsd-python/actions/workflows/run-pytest.yml)

# gridappsd-python
Python library for developing applications and services against the gridappsd api

## Requirements

The gridappsd-python library requires a  python version >= 3.6 and < 4 in order to work properly (Note no testing
has been done with python 4 to date).

## Installation

The recommended installation of `gridappsd-python` is in a separate virtual environment.  Executing the following
will create an environment called `griddapps-env`.

```shell
python3 -m venv gridappsd-env
```

Sourcing the gridappsd-env activates the newly created python environment.

```shell
source gridappsd-env/bin/activate
```

Upgrade pip to the latest (some packages require 19.0+ version of pip).

```shell
python -m pip install pip --upgrade
```

Install the latest `gridappsd-python` and its dependencies in the virtual environment.

```shell
pip install gridappsd-python
```

### Verifying things are working properly

The following code snippet assumes you have created a gridappsd instance using the steps in
https://github.com/GRIDAPPSD/gridappsd-docker.

Create a test script (tester.py) with the following content.

```python

from gridappsd import GridAPPSD

def on_message_callback(header, message):
    print(f"header: {header} message: {message}")

# Note these should be changed on the server in a cyber secure environment!
username = "app_user"
password = "1234App"

# Note: there are other parameters for connecting to
# systems other than localhost
gapps = GridAPPSD(username=username, password=password)

assert gapps.connected

gapps.send('send.topic', {"foo": "bar"})

# Note we are sending the function not executing the function in the second parameter
gapps.subscribe('subscribe.topic', on_message_callback)

gapps.send('subcribe.topic', 'A message about subscription')

time.sleep(5)

gapps.close()

```

Start up the gridappsd-docker enabled platform.  Then run the following to execute the tester.py script

```shell
python tester.py
```

## Application Developers

### Deployment

Please see [DOCKER_CONTAINER.md](DOCKER_CONTAINER.md) for working within the docker application base container.

### Local Development

Developing applications against gridappsd using the `gridappsd-python` library should follow the same steps
as above, however with a couple of environmental variables specified.  The following environmental variables are
available to provide the same context that would be available from inside the application docker container.  These
are useful to know for developing your application outside of the docker context (e.g. in a python notebook).

***NOTE: you can also define these your ~./bashrc file so you don't have to specify them all the time***

```shell
# export allows all processes started by this shell to have access to the global variable

# address where the gridappsd server is running - default localhost
export GRIDAPPSD_ADDRESS=localhost

# port to connect to on the gridappsd server (the stomp client port)
export GRIDAPPSD_PORT=61613

# username to connect to the gridappsd server
export GRIDAPPSD_USER=app_user

# password to connect to the gridappsd server
export GRIDAPPSD_PASSWORD=1234App

# Note these should be changed on the server in a cyber secure environment!
```

The following is the same tester code as above, but with the environment variables set.  The environment variables
should be set in your environment when running the application inside our docker container.

```python

from gridappsd import GridAPPSD

def on_message_callback(header, message):
    print(f"header: {header} message: {message}")

# Create GridAPPSD object and connect to the gridappsd server.
gapps = GridAPPSD()

assert gapps.connected

gapps.send('send.topic', {"foo": "bar"})

# Note we are sending the function not executing the function in the second parameter
gapps.subscribe('subscribe.topic', on_message_callback)

gapps.send('subcribe.topic', 'A message about subscription')

time.sleep(5)

gapps.close()

```

## Developers

This project uses poetry to build the environment for execution.  Follow the instructions
https://python-poetry.org/docs/#installation to install poetry.  As a developer I prefer not to have poetry installed
in the same virtual environment that my projects are in.

Clone the github repository:

```shell
git clone https://github.com/GRIDAPPSD/gridappsd-python -b develop
cd gridappsd-python
```

The following commands build and install a local wheel into an environment created just for this package.

```shell
# Build the project (stores in dist directory both .tar.gz and .whl file)
poetry build

# Install the wheel into the environment and the dev dependencies
poetry install

# Install only the library dependencies
poetry install --no-dev
```

***Note:*** Poetry does not have a setup.py that you can install in editable mode like with pip install -e ., however
you can extract the generated setup.py file from the built tar.gz file in the dist directory.  Just extract the
.tar.gz file and copy the setup.py file from the extracted directory to the root of gridappsd-python.  Then you can
enable editing through pip install -e. as normal.


## Testing

Testing has become an integral part of the software lifecycle.  The `gridappsd-python` library has both unit and
integration tests available to be run.  In order to execute these, you must have installed the gridappsd-python library
as above with dev-dependencies.

During the testing phase the docker containers required for the tests are downloaded from
dockerhub and started.  By default the `develop` tag is used to test the library using pytest.  
One can customize the docker image tag by setting the environmental
variable `GRIDAPPSD_TAG_ENV` either by `export GRIDAPPSD_TAG_ENV=other_tag` or by executing 
pytest with the following:

```shell script

# Export environmental variables and all tests will use the same tag (other_tag) to pull from docker hub.
# Default tag is develop
export GRIDAPPSD_TAG_ENV=other_tag
pytest

# Tests also require the username and password to be avaialable as environmental variables 
# in order for them to properly run these tests
export GRIDAPPSD_USER=user
export GRIDAPPSD_PASSWORD=pass

pytest
```

 ***NOTE: the first running the tests will download all of the docker images associated with the
 [GOSS-GridAPPS-D](http://github.com/GRIDAPPSD/GOSS-GridAPPS-D) repository.  This process may take some time.***
 
### Running tests created in a new project

The `gridappsd-python` library exposes a testing environment through the `gridappsd.docker_handler` module.  Including the following
`conftest.py` in the root of your base test directory allows tests to reference these.  Using these fixtures will start all of the
base containers required for `gridappsd` to run.  

```python

# conftest.py
# Create a conftest.py file in the root of the tests directory to enable usage throughout the tests directory and below. 
# 
# Tested project structure an layout
#
# project-folder\
#   mainmodule\
#     __init__.py
#     myapplication.py
#   tests\
#     conftest.py
#     test_myapplication.py
#   README.md

import logging
import os
import sys

import pytest

from gridappsd import GridAPPSD, GOSS
from gridappsd.docker_handler import run_dependency_containers, run_gridappsd_container, Containers

levels = dict(
    CRITICAL=50,
    FATAL=50,
    ERROR=40,
    WARNING=30,
    WARN=30,
    INFO=20,
    DEBUG=10,
    NOTSET=0
)

# Get string representation of the log level passed
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Make sure the level passed is one of the valid levels.
if LOG_LEVEL not in levels.keys():
    raise AttributeError("Invalid LOG_LEVEL environmental variable set.")

# Set the numeric version of log level to pass to the basicConfig function
LOG_LEVEL = levels[LOG_LEVEL]

logging.basicConfig(stream=sys.stdout, level=LOG_LEVEL,
                    format="%(asctime)s|%(levelname)s|%(name)s|%(message)s")
logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)
logging.getLogger("docker.utils.config").setLevel(logging.INFO)
logging.getLogger("docker.auth").setLevel(logging.INFO)


STOP_CONTAINER_AFTER_TEST = os.environ.get('GRIDAPPSD_STOP_CONTAINERS_AFTER_TESTS', True)


@pytest.fixture(scope="module")
def docker_dependencies():
    print("Docker dependencies")
    # Containers.reset_all_containers()

    with run_dependency_containers(stop_after=STOP_CONTAINER_AFTER_TEST) as dep:
        yield dep
    print("Cleanup docker dependencies")


@pytest.fixture
def gridappsd_client(request, docker_dependencies):
    with run_gridappsd_container(stop_after=STOP_CONTAINER_AFTER_TEST):
        gappsd = GridAPPSD()
        gappsd.connect()
        assert gappsd.connected
        models = gappsd.query_model_names()
        assert models is not None
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

Using the above fixtures from inside a test module and test function looks like the following:

```python

# Example test function using the gridappsd_client fixture 

@mock.patch.dict(os.environ, {"GRIDAPPSD_APPLICATION_ID": "helics_goss_bridge.py"})
def test_gridappsd_status(gridappsd_client):
    gappsd = gridappsd_client
    assert "helics_goss_bridge.py" == gappsd.get_application_id()
    assert gappsd.get_application_status() == ProcessStatusEnum.STARTING.value
    assert gappsd.get_service_status() == ProcessStatusEnum.STARTING.value
    gappsd.set_application_status("RUNNING")

    assert gappsd.get_service_status() == ProcessStatusEnum.RUNNING.value
    assert gappsd.get_application_status() == ProcessStatusEnum.RUNNING.value

    gappsd.set_service_status("COMPLETE")
    assert gappsd.get_service_status() == ProcessStatusEnum.COMPLETE.value
    assert gappsd.get_application_status() == ProcessStatusEnum.COMPLETE.value

    # Invalid
    gappsd.set_service_status("Foo")
    assert gappsd.get_service_status() == ProcessStatusEnum.COMPLETE.value
    assert gappsd.get_application_status() == ProcessStatusEnum.COMPLETE.value

```

