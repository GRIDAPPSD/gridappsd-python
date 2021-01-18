import os

import pytest

from gridappsd import GridAPPSD, GOSS
from gridappsd.docker_handler import run_dependency_containers, run_gridappsd_container, Containers

STOP_CONTAINER_AFTER_TEST = os.environ.get('GRIDAPPSD_STOP_CONTAINERS_AFTER_TESTS', True)

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

@pytest.fixture
def goss_client(docker_dependencies):
    with run_gridappsd_container(stop_after=STOP_CONTAINER_AFTER_TEST):
        goss = GOSS()
        goss.connect()
        assert goss.connected

        yield goss

        goss.disconnect()
