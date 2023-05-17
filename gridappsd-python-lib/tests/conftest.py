import logging
import os
import shutil
import sys
import time
from pathlib import Path

import git
import pytest
from python_on_whales import docker
from python_on_whales.docker_client import DockerClient

from gridappsd import GOSS, GridAPPSD

# from gridappsd.docker_handler import (Containers, run_dependency_containers,
#                                       run_gridappsd_container)

levels = dict(CRITICAL=50,
              FATAL=50,
              ERROR=40,
              WARNING=30,
              WARN=30,
              INFO=20,
              DEBUG=10,
              NOTSET=0)

# Get string representation of the log level passed
LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")

# Make sure the level passed is one of the valid levels.
if LOG_LEVEL not in levels.keys():
    raise AttributeError("Invalid LOG_LEVEL environmental variable set.")

# Set the numeric version of log level to pass to the basicConfig function
LOG_LEVEL_INT = levels[LOG_LEVEL]

logging.basicConfig(stream=sys.stdout,
                    level=LOG_LEVEL_INT,
                    format="%(asctime)s|%(levelname)s|%(name)s|%(message)s")
logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)
logging.getLogger("docker.utils.config").setLevel(logging.INFO)
logging.getLogger("docker.auth").setLevel(logging.INFO)

_log = logging.getLogger(__name__)

STOP_CONTAINER_AFTER_TEST = os.environ.get(
    'GRIDAPPSD_STOP_CONTAINERS_AFTER_TESTS', False)
os.environ['GRIDAPPSD_USER'] = 'system'
os.environ['GRIDAPPSD_PASSWORD'] = 'manager'
os.environ['GRIDAPPSD_TAG'] = ':develop'
os.environ["GRIDAPPSD_ADDRESS"] = "localhost"
os.environ["GRIDAPPSD_PORT"] = "61613"

gridappsd_docker_url = "https://github.com/GRIDAPPSD/gridappsd-docker"
gridappsd_docker_clone_path = Path("/tmp/gridappsd-docker")


def clone_gridappsd_docker():

    if gridappsd_docker_clone_path.exists():
        # TODO: Do something with the repo...checkout revert etc.
        pass
        #repo = git.Repo(str(gridappsd_docker_clone_path))
    else:
        git.Repo.clone_from(url=gridappsd_docker_url,
                            to_path=str(gridappsd_docker_clone_path),
                            branch="main",
                            depth=1)


@pytest.fixture(scope="session")
def docker_compose_up() -> DockerClient:
    clone_gridappsd_docker()
    path = str(gridappsd_docker_clone_path / "docker-compose.yml")
    assert os.path.exists(path)
    dc = DockerClient(compose_files=[path])

    config = dc.compose.config(return_json=False)
    if "sample_app" in config.services:
        assert config.services["sample_app"]
        del config.services["sample_app"]

    dc.compose.up(detach=True, start=True, wait=True, recreate=True)
    should_not_exit = True

    while should_not_exit:
        log_stream = dc.logs(container="gridappsd", stream=True)

        for stream_type, stream_content in log_stream:
            decoded_content = stream_content.decode('utf-8').strip()
            if "gridappsd-topology-processor|None|STARTED" in decoded_content:
                should_not_exit = False
                break
            _log.debug(decoded_content)
        time.sleep(0.2)

    yield dc

    dc.compose.down()
    # shutil.rmtree(gridappsd_docker_clone_path, ignore_errors=True)


# @pytest.fixture(scope="module")
# def docker_dependencies():
#     print("Docker dependencies")
#     # Containers.reset_all_containers()

#     with run_dependency_containers(
#             stop_after=STOP_CONTAINER_AFTER_TEST) as dep:
#         yield dep
#     print("Cleanup docker dependencies")


@pytest.fixture
def gridappsd_client(request, docker_compose_up: DockerClient):

    dc = docker_compose_up
    

    gappsd = GridAPPSD()
    assert gappsd.connected

    yield gappsd

    gappsd.disconnect()

    # with run_gridappsd_container(stop_after=STOP_CONTAINER_AFTER_TEST):
    #     gappsd = GridAPPSD()
    #     gappsd.connect()
    #     assert gappsd.connected
    #     models = gappsd.query_model_names()
    #     assert models is not None
    #     if request.cls is not None:
    #         request.cls.gridappsd_client = gappsd
    #     yield gappsd

    #     gappsd.disconnect()


# @pytest.fixture
# def goss_client(docker_dependencies):
#     with run_gridappsd_container(stop_after=STOP_CONTAINER_AFTER_TEST):
#         goss = GOSS()
#         goss.connect()
#         assert goss.connected

#         yield goss
