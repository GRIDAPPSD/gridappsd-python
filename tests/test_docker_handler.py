import inspect
import logging
import os
import time
import sys

import docker

from gridappsd import GridAPPSD
from gridappsd.docker_handler import (run_dependency_containers, Containers, run_gridappsd_container,
                                      stream_container_log_to_file, DEFAULT_DOCKER_DEPENDENCY_CONFIG)

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
_log = logging.getLogger(inspect.getmodulename(__file__))


def test_log_container(docker_dependencies):
    mypath = "/tmp/alphabetagamma.txt"
    stream_container_log_to_file("influxdb", mypath)
    time.sleep(5)
    print("After call to stream")
    assert os.path.exists(mypath)
    with open(mypath, 'rb') as rf:
        assert len(rf.readlines()) > 0


def test_can_reset_all_containers():
    Containers.reset_all_containers()
    assert not Containers.container_list()

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
    assert len(Containers.container_list()) == 1
    time.sleep(5)
    Containers.reset_all_containers()
    assert not Containers.container_list()


def test_stream_log_to_file():
    pass


def test_can_dependencies_continue_after_context_manager():
    my_config = DEFAULT_DOCKER_DEPENDENCY_CONFIG.copy()
    Containers.reset_all_containers()

    time.sleep(3)
    with run_dependency_containers() as containers:
        time.sleep(10)

    assert len(Containers.container_list()) == 5

    containers = Containers.container_list()
    for name in my_config:
        found = False
        for c in containers:
            if c.name == name:
                found = True
                break
        assert found, f"Missing container {name} in list."

    Containers.reset_all_containers()


def test_multiple_runs_in_a_row_with_dependency_context_manager():

    Containers.reset_all_containers()

    with run_dependency_containers():
        pass

    assert len(Containers.container_list()) == 5

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

    # There shouldn't be any containers now because both contexts were cleaned up.
    assert not len(Containers.container_list())


def test_can_start_gridapps():
    Containers.reset_all_containers()
    with run_dependency_containers(False) as cont:
        with run_gridappsd_container(False) as cont2:
            g = GridAPPSD()
            assert g.connected

