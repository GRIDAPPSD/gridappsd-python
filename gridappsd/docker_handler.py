#!/usr/bin/env python3

from copy import deepcopy
import logging
import os
from pathlib import Path
import re
import shutil
import time
import urllib.request
import contextlib

_log = logging.getLogger(__file__)

try:
    import docker
    HAS_DOCKER = True
except ImportError:
    _log.warning("Docker api not loaded. pip install docker to install as package.")
    HAS_DOCKER = False

if HAS_DOCKER:

    def expand_all(user_path):
        return os.path.expandvars(os.path.expanduser(user_path))


    # This path needs to be the path to the repo where the data is done.
    GRIDAPPSD_TEST_REPO = expand_all(os.environ.get("GRIDAPPSD_TEST_REPO", Path(__file__).parent.parent))
    GRIDAPPSD_DATA_REPO = expand_all(os.environ.get("GRIDAPPSD_DATA_REPO", "/tmp/gridappsd_temp_data"))

    if not Path(GRIDAPPSD_TEST_REPO).is_dir():
        raise AttributeError(f"Invalid GRIDAPPSD_TEST_REPO {GRIDAPPSD_TEST_REPO}")

    if not Path(GRIDAPPSD_TEST_REPO).joinpath("conf").is_dir():
        raise AttributeError(f"Invalid conf directory must be located {Path(GRIDAPPSD_TEST_REPO).joinpath('conf')}")
    os.makedirs(GRIDAPPSD_DATA_REPO, exist_ok=True)

    repo_dir = GRIDAPPSD_TEST_REPO
    data_dir = GRIDAPPSD_DATA_REPO

    assert os.path.exists(repo_dir + "/conf/entrypoint.sh")
    assert os.path.exists(repo_dir + "/conf/run-gridappsd.sh")

    def mysql_setup():
        # Downlaod mysql file
        _log.debug("Downloading mysql data file from Bootstrap repository")
        mysql_dir = f'{data_dir}/dumps'
        mysql_file = f'{mysql_dir}/gridappsd_mysql_dump.sql'
        if os.path.isdir(mysql_file):
            raise RuntimeError(f"mysql datafile is directory, delete {mysql_file} using sudo rm -rf {mysql_file}")
        if not os.path.isdir(mysql_dir):
            os.makedirs(mysql_dir, 0o0775, exist_ok=True)
        urllib.request.urlretrieve('https://raw.githubusercontent.com/GRIDAPPSD/Bootstrap/master/gridappsd_mysql_dump.sql',
                                   filename=mysql_file)

        # Modify the mysql file to allow connections from gridappsd container
        with open(mysql_file, "r") as sources:
            lines = sources.readlines()
        with open(mysql_file, "w") as sources:
            for line in lines:
                sources.write(re.sub(r'localhost', '%', line))


    default_docker_dependencies = {
        "influxdb": {
            "start": True,
            "image": "gridappsd/influxdb:develop",
            "pull": True,
            "ports": {"8086/tcp": 8086},
            "environment": {"INFLUXDB_DB": "proven"},
            "links": "",
            "volumes": "",
            "entrypoint": "",
        },
        "redis": {
            "start": True,
            "image": "redis:3.2.11-alpine",
            "pull": True,
            "ports": {"6379/tcp": 6379},
            "environment": [],
            "links": "",
            "volumes": "",
            "entrypoint": "redis-server --appendonly yes",
        },
        "blazegraph": {
            "start": True,
            "image": "gridappsd/blazegraph:develop",
            "pull": True,
            "ports": {"8080/tcp": 8889},
            "environment": [],
            "links": "",
            "volumes": "",
            "entrypoint": "",
        },
        "mysql": {
            "start": True,
            "image": "mysql/mysql-server:5.7",
            "pull": True,
            "ports": {"3306/tcp": 3306},
            "environment": {
                "MYSQL_RANDOM_ROOT_PASSWORD": "yes",
                "MYSQL_PORT": "3306"
            },
            "links": "",
            "volumes": {
                data_dir + "/dumps/gridappsd_mysql_dump.sql": {"bind": "/docker-entrypoint-initdb.d/schema.sql",
                                                               "mode": "ro"}
            },
            "entrypoint": "",
            "onsetupfn": mysql_setup
        },
        "proven": {
            "start": True,
            "image": "gridappsd/proven:develop",
            "pull": True,
            "ports": {"8080/tcp": 18080},
            "environment": {
                "PROVEN_SERVICES_PORT": "18080",
                "PROVEN_SWAGGER_HOST_PORT": "localhost:18080",
                "PROVEN_USE_IDB": "true",
                "PROVEN_IDB_URL": "http://influxdb:8086",
                "PROVEN_IDB_DB": "proven",
                "PROVEN_IDB_RP": "autogen",
                "PROVEN_IDB_USERNAME": "root",
                "PROVEN_IDB_PASSWORD": "root",
                "PROVEN_T3DIR": "/proven"},
            "links": {"influxdb": "influxdb"},
            "volumes": "",
            "entrypoint": "",
        }
    }

    default_gridappsd_docker = {
        "gridappsd": {
            "start": True,
            "image": "gridappsd/gridappsd:develop",
            "pull": True,
            "ports": {"61613/tcp": 61613, "61614/tcp": 61614, "61616/tcp": 61616},
            "environment": {
                "PATH": "/gridappsd/bin:/gridappsd/lib:/gridappsd/services/fncsgossbridge/service:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin",
                "DEBUG": 1,
                "START": 1
            },
            "links": {"mysql": "mysql", "influxdb": "influxdb", "blazegraph": "blazegraph", "proven": "proven",
                      "redis": "redis"},
            "volumes": {
                repo_dir + "/conf/entrypoint.sh": {"bind": "/gridappsd/entrypoint.sh", "mode": "rw"},
                repo_dir + "/conf/run-gridappsd.sh": {"bind": "/gridappsd/run-gridappsd.sh", "mode": "rw"}
            },
            "entrypoint": "",
        }
    }


    class Containers:
        """
        This class allows the creation/management of containers created by the gridappsd
        docker process.
        """
        def __init__(self, container_def):
            self._container_def = container_def

        @staticmethod
        def reset_all_containers():
            client = docker.from_env()

            for container in client.containers.list():
                container.kill()

        def check_required_running(self, config):
            my_config = deepcopy(config)
            client = docker.from_env()

            for c in client.containers.list():
                my_config.pop(c.name, None)

            assert not my_config, f"The required containers were not satisfied missing {list(my_config.keys())}"

        def start(self):
            client = docker.from_env()
            for service, value in self._container_def.items():
                if self._container_def[service]['pull']:
                    _log.debug(f"Pulling {service} : {self._container_def[service]['image']}")
                    client.images.pull(self._container_def[service]['image'])

            for service, value in self._container_def.items():
                # Provide a way to dynamically create things that the container will need
                # on the host system.
                if value.get('onsetupfn'):
                    value.get('onsetupfn')()
                if self._container_def[service]['start']:
                    _log.debug(f"Starting {service} : {self._container_def[service]['image']}")
                    kwargs = {}
                    kwargs['image'] = self._container_def[service]['image']
                    # Only name the containers if remove is on
                    kwargs['remove'] = True
                    kwargs['name'] = service
                    kwargs['detach'] = True
                    if self._container_def[service]['environment']:
                        kwargs['environment'] = value['environment']
                    if self._container_def[service]['ports']:
                        kwargs['ports'] = value['ports']
                    if self._container_def[service]['volumes']:
                        kwargs['volumes'] = value['volumes']
                    if self._container_def[service]['entrypoint']:
                        kwargs['entrypoint'] = value['entrypoint']
                    if self._container_def[service]['links']:
                        kwargs['links'] = value['links']
                    # print (kwargs)
                    container = client.containers.run(**kwargs)
                    self._container_def[service]['containerid'] = container.id
            print([x.name for x in client.containers.list()])

        def stop(self):
            client = docker.from_env()
            for service, value in self._container_def.items():
                if value.get('containerid'):
                    try:
                        cnt = client.containers.get(value.get('containerid'))
                        cnt.kill()
                        # client.containers.get(value.get('containerid')).kill() # value.get('name')).kill()
                    except docker.errors.NotFound:
                        pass


    @contextlib.contextmanager
    def run_containers(config, stop_after=True):
        containers = Containers(config)

        containers.start()
        try:
            yield containers
        finally:
            if stop_after:
                containers.stop()


    @contextlib.contextmanager
    def run_dependency_containers(stop_after=False):

        containers = Containers(default_docker_dependencies)

        containers.start()
        try:
            yield containers
        finally:
            if stop_after:
                containers.stop()


    @contextlib.contextmanager
    def run_gridappsd_container(stop_after=True):
        """ A contextmanager that uses """

        containers = Containers(default_gridappsd_docker)

        containers.start()
        try:
            yield containers
        finally:
            if stop_after:
                containers.stop()
