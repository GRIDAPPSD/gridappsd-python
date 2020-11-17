import os

import pytest

from gridappsd import GOSS, GridAPPSD
from gridappsd.docker_handler import run_dependency_containers, run_gridappsd_container, Containers, \
    update_gridappsd_tag

GRIDAPPSD_TAG_ENV = os.environ.get('GRIDAPPSD_TAG', 'develop')
STOP_CONTAINER_AFTER_TEST = False

@pytest.fixture(scope="module")
def docker_dependencies():
    print("Docker dependencies")
    Containers.reset_all_containers()

    update_gridappsd_tag(GRIDAPPSD_TAG_ENV)

    with run_dependency_containers(stop_after=STOP_CONTAINER_AFTER_TEST) as dep:
        yield dep
    print("Cleanup docker dependencies")


@pytest.fixture
def goss_client(docker_dependencies):
    with run_gridappsd_container(stop_after=STOP_CONTAINER_AFTER_TEST):
        goss = GOSS()
        goss.connect()
        assert goss.connected

        yield goss

        goss.disconnect()


@pytest.fixture
def gridappsd_client(docker_dependencies):
    with run_gridappsd_container(stop_after=STOP_CONTAINER_AFTER_TEST):
        gappsd = GridAPPSD()
        gappsd.connect()
        assert gappsd.connected

        yield gappsd

        gappsd.disconnect()
