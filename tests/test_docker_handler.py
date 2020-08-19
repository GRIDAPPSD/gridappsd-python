import inspect
import logging
import time
from copy import deepcopy
import sys

import docker

from gridappsd import GridAPPSD
from gridappsd.docker_handler import (run_dependency_containers, Containers, run_gridappsd_container, run_containers,
                                      DEFAULT_DOCKER_DEPENDENCY_CONFIG, DEFAULT_GRIDAPPSD_DOCKER_CONFIG)

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
_log = logging.getLogger(inspect.getmodulename(__file__))


def test_can_reset_all_containers():
    client = docker.from_env()
    for c in client.containers.list():
        c.kill()

    assert not client.containers.list()
    config = {
        "redis": {
            "start": True,
            "image": "redis:3.2.11-alpine",
            "pull": True,
            "ports": {"6379/tcp": 6379},
            "environment": [],
            "links": "",
            "volumes": "",
            "entrypoint": "redis-server --appendonly yes",
        }
    }
    cont = Containers(config)
    cont.start()
    assert len(client.containers.list()) == 1
    time.sleep(5)
    Containers.reset_all_containers()
    assert not client.containers.list()
    cont.stop()


def test_can_dependencies_continue_after_context_manager():

    Containers.reset_all_containers()

    time.sleep(3)
    with run_dependency_containers() as containers:
        time.sleep(10)

    client = docker.from_env()
    assert len(client.containers.list()) == 5


def test_multiple_runs_in_a_row_with_dependency_context_manager():

    Containers.reset_all_containers()

    with run_dependency_containers():
        pass

    client = docker.from_env()

    assert len(client.containers.list()) == 5

    with run_gridappsd_container():
        timeout = 0
        gapps = None

        while timeout < 30:
            try:
                gapps = GridAPPSD()
                gapps.connect()
                break
            except:
                time.sleep(1)
                timeout += 1

        assert gapps
        assert gapps.connected

    with run_gridappsd_container():
        timeout = 0
        gapps = None
        time.sleep(10)
        while timeout < 30:
            try:
                gapps = GridAPPSD()
                gapps.connect()
                break
            except:
                time.sleep(1)
                timeout += 1

        assert gapps
        assert gapps.connected


def test_can_start_gridappsd_within_dependency_context_manager_all_cleanup():

    Containers.reset_all_containers()

    # config = deepcopy(default_docker_dependencies)
    # config.update(deepcopy(default_gridappsd_docker))

    with run_dependency_containers(True) as cont:
        # True in this method will remove the containsers
        with run_gridappsd_container(True) as dep_con:
            # Default cleanup is true within run_gridappsd_container method
            timeout = 0
            gapps = None
            time.sleep(10)
            while timeout < 30:
                try:
                    gapps = GridAPPSD()
                    gapps.connect()
                    break
                except:
                    time.sleep(1)
                    timeout += 1

            assert gapps
            assert gapps.connected

    client = docker.from_env()
    # There shouldn't be any containers now because both contexts were cleaned up.
    assert not len(client.containers.list())


#def test_can_run_dependency_containers_twice():
