import pytest
from gridappsd import GOSS, GridAPPSD
from gridappsd.docker_handler import run_dependency_containers, run_gridappsd_container, Containers


@pytest.fixture(scope="module")
def docker_dependencies():
    print("Docker dependencies")
    Containers.reset_all_containers()

    with run_dependency_containers(stop_after=True) as dep:
        yield dep
    print("Cleanup docker dependencies")


@pytest.fixture
def goss_client(docker_dependencies):
    with run_gridappsd_container(True):
        goss = GOSS()
        goss.connect()
        assert goss.connected

        yield goss

        goss.disconnect()


@pytest.fixture
def gridappsd_client(docker_dependencies):
    with run_gridappsd_container(True):
        gappsd = GridAPPSD()
        gappsd.connect()
        assert gappsd.connected

        yield gappsd

        gappsd.disconnect()
