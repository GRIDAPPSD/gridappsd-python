import inspect
import logging
import os
from pathlib import Path

import docker
import sys
import time

from gridappsd import GridAPPSD
from gridappsd.docker_handler import (run_dependency_containers, Containers, run_gridappsd_container,
                                      stream_container_log_to_file, DEFAULT_DOCKER_DEPENDENCY_CONFIG,
                                      mysql_setup, MYSQL_SCHEMA_INIT_DIR)

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


def test_can_dependencies_continue_after_context_manager():
    my_config = DEFAULT_DOCKER_DEPENDENCY_CONFIG.copy()
    Containers.reset_all_containers()

    time.sleep(3)
    my_dep_containers = None
    with run_dependency_containers() as containers:
        my_dep_containers = containers
        time.sleep(10)

    real_containers = Containers.container_list()
    for k in my_dep_containers.container_def.keys():
        found = False
        for c in real_containers:
            if c.name == k:
                found = True
                break
        assert found, f"Couldn't find {k} container in list"

    Containers.reset_all_containers()


def test_create_volume_container():
    Containers.create_volume_container("test_volume", "test_volume", "/startup", restart_if_exists=True)
    path = str(Path("gridappsd/conf").absolute())
    Containers.copy_to(path, "test_volume:/startup/conf")
    client = docker.from_env()
    result = client.containers.get("test_volume").exec_run("ls -l /startup")
    assert True


def test_can_upload_files_to_container():
    Containers.reset_all_containers()

    client = docker.from_env()
    client.images.pull("alpine")
    test_container = client.containers.run(image="alpine", command="tail -f /dev/null",
                                           detach=True,
                                           name="test_upload_container",
                                           remove=True)
    # may take a few for image to be up
    time.sleep(20)
    conf_path = str(Path("gridappsd/conf").absolute())
    Containers.copy_to(conf_path, f"{test_container.name}:/conf")
    results = test_container.exec_run("ls -l /conf")
    for f in os.listdir(conf_path):
        assert f in results.output.decode("utf-8"), f"{f} was not in /conf"


def test_multiple_runs_in_a_row_with_dependency_context_manager():

    Containers.reset_all_containers()

    with run_dependency_containers():
        pass

    containers = [x for x in Containers.container_list() if "config" not in x.name]
    assert len(containers) == 5

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

    # Filter out the two config containers that we start up for volume data.
    containers = [x.name for x in Containers.container_list() if "config" not in x.name]
    assert not len(containers)


def test_can_start_gridapps():
    Containers.reset_all_containers()
    with run_dependency_containers() as cont:
        with run_gridappsd_container() as cont2:
            g = GridAPPSD()
            assert g.connected


def test_mysql_setup():
    mysql_setup()
    assert Path(MYSQL_SCHEMA_INIT_DIR).exists()
    assert Path(MYSQL_SCHEMA_INIT_DIR).joinpath("gridappsd_mysql_dump.sql").is_file()

