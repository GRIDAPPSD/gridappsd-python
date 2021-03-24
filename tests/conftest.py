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
LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")

# Make sure the level passed is one of the valid levels.
if LOG_LEVEL not in levels.keys():
    raise AttributeError("Invalid LOG_LEVEL environmental variable set.")

# Set the numeric version of log level to pass to the basicConfig function
LOG_LEVEL = levels[LOG_LEVEL]

logging.basicConfig(stream=sys.stdout, level=LOG_LEVEL)

STOP_CONTAINER_AFTER_TEST = os.environ.get('GRIDAPPSD_STOP_CONTAINERS_AFTER_TESTS', True)


@pytest.fixture(scope="module")
def docker_dependencies():
    print("Docker dependencies")
    Containers.reset_all_containers()

    with run_dependency_containers(stop_after=STOP_CONTAINER_AFTER_TEST) as dep:
        yield dep
    print("Cleanup docker dependencies")


@pytest.fixture
def gridappsd_client(request, docker_dependencies):
    with run_gridappsd_container(stop_after=STOP_CONTAINER_AFTER_TEST):
        gappsd = GridAPPSD()
        gappsd.connect()
        assert gappsd.connected

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


@pytest.fixture
def foo(request):
    request.cls.gridappsd_client = ["alpha", "beta", "gamma"]

