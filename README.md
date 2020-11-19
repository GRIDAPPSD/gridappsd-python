![Build status](https://github.com/GRIDAPPSD/gridappsd-python/workflows/Python%20package/badge.svg)

# gridappsd-python
Python library for developing applications and services against the gridappsd api

## Installation

The `gridappsd-python` library requires python 3.6+ in order to work.
- Clone repository
- Install into your python environment `pip install . `

## Creating a connection to GridAPPS-D

```` python

from gridappsd import GridAPPSD

def on_message_callback(header, message):
    print(f"header: {header} message: {message}")

# Note: there are other parameters for connecting to 
# systems other than localhost
gapps = GridAPPSD(username="user", password="pass")

assert gapps.connected

gapps.send('send.topic', {"foo": "bar"})

# Note we are sending the function not executing the function in the second parameter
gapps.subscribe('subscribe.topic', on_message_callback)

gapps.send('subcribe.topic', 'A message about subscription')

time.sleep(5)

gapps.close()

````


## Testing

Before running the tests for `gridappsd-python` one should install the test requirements.

```shell script

# Install gridappsd requirements
pip install -r requirements.txt

# Install gridappsd
pip install .

# Install testing requirements
pip install -r test_requirements.txt
```

During the testing phase the docker containers required for the tests are downloaded from
dockerhub and started.  By default the `develop` tag is used to test the library using pytest.  
One can customize the docker image tag by setting the environmental
variable `GRIDAPPSD_TAG_ENV` either by `export GRIDAPPSD_TAG_ENV=other_tag` or by executing 
pytest with the following:

```shell script

# All tests run will use the same tag (other_tag) to pull from docker hub.
GRIDAPPSD_TAG_ENV=other_tag pytest
```

 __NOTE: the first running the tests will download all of the docker images associated with the [GOSS-GridAPPS-D](http://github.com/GRIDAPPSD/GOSS-GridAPPS-D) repository.  
 may take a while.__
 
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

import os

import pytest

from gridappsd import GridAPPSD
from gridappsd.docker_handler import run_dependency_containers, run_gridappsd_container, Containers

# If set to False then None of the containers will clean up after themselves.
# If more than one test is ran then this will cause an error because the gridappsd
# container will not be cleansed.
STOP_CONTAINER_AFTER_TEST = os.environ.get("GRIDAPPSD_STOP_CONTAINERS_AFTER_TESTS", True)

if isinstance(STOP_CONTAINER_AFTER_TEST, str):
    if STOP_CONTAINER_AFTER_TEST.lower() == 'false' or STOP_CONTAINER_AFTER_TEST.lower() != '0':
        STOP_CONTAINER_AFTER_TEST = False
    else:
        STOP_CONTAINER_AFTER_TEST = True


@pytest.fixture(scope="module")
def docker_dependencies():
    print("Docker dependencies")
    Containers.reset_all_containers()

    with run_dependency_containers(stop_after=STOP_CONTAINER_AFTER_TEST) as dep:
        yield dep
    print("Cleanup docker dependencies")


@pytest.fixture
def gridappsd_client(docker_dependencies):
    with run_gridappsd_container(stop_after=STOP_CONTAINER_AFTER_TEST):
        gappsd = GridAPPSD()
        gappsd.connect()
        assert gappsd.connected

        yield gappsd

        gappsd.disconnect()

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

