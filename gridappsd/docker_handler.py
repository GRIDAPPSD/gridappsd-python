#!/usr/bin/env python3

from copy import deepcopy
from datetime import datetime, timedelta
import logging
import os
from pprint import pprint
from subprocess import PIPE
import threading
from typing import Optional, Union

import pkg_resources
from pathlib import Path
import re
import shutil
import sys
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
    GRIDAPPSD_CONF_DIR = expand_all(os.environ.get("GRIDAPPSD_CONF_DIR",
                                                   pkg_resources.resource_filename('gridappsd', 'conf')))
    GRIDAPPSD_DATA_REPO = expand_all(os.environ.get("GRIDAPPSD_DATA_REPO", "/tmp/gridappsd_temp_data"))

    if not Path(GRIDAPPSD_CONF_DIR).is_dir():
        raise AttributeError(f"Invalid GRIDAPPSD_CONF_REPO {GRIDAPPSD_CONF_DIR}")

    os.makedirs(GRIDAPPSD_DATA_REPO, exist_ok=True)
    if not Path(GRIDAPPSD_DATA_REPO).exists():
        raise AttributeError(f"Invalid GRIDAPPSD_DATA_REPO couldn't make or doesn't exist {GRIDAPPSD_DATA_REPO}")

    data_dir = GRIDAPPSD_DATA_REPO

    assert Path(GRIDAPPSD_CONF_DIR).joinpath("entrypoint.sh").exists()
    assert Path(GRIDAPPSD_CONF_DIR).joinpath("run-gridappsd.sh").exists()


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

    # Use the environmental variable if specified otherwise use the develop tag.
    DEFAULT_GRIDAPPSD_TAG = os.environ.get('GRIDAPPSD_TAG_ENV', 'develop')

    __TPL_DEPENDENCY_CONFIG__ = {
        "influxdb": {
            "start": True,
            "image": "gridappsd/influxdb:{{DEFAULT_GRIDAPPSD_TAG}}",
            "pull": True,
            "ports": {"8086/tcp": 8086},
            "environment": {"INFLUXDB_DB": "proven"}
        },
        "redis": {
            "start": True,
            "image": "redis:3.2.11-alpine",
            "pull": True,
            "ports": {"6379/tcp": 6379},
            "environment": [],
            "entrypoint": "redis-server --appendonly yes",
        },
        "blazegraph": {
            "start": True,
            "image": "gridappsd/blazegraph:{{DEFAULT_GRIDAPPSD_TAG}}",
            "pull": True,
            "ports": {"8080/tcp": 8889},
            "environment": []
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
            "volumes": {
                data_dir + "/dumps/gridappsd_mysql_dump.sql": {"bind": "/docker-entrypoint-initdb.d/schema.sql",
                                                               "mode": "ro"}
            },
            "onsetupfn": mysql_setup
        },
        "proven": {
            "start": True,
            "image": "gridappsd/proven:{{DEFAULT_GRIDAPPSD_TAG}}",
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
            "links": {"influxdb": "influxdb"}
        }
    }

    __TPL_GRIDAPPSD_CONFIG__ = {
        "gridappsd": {
            "start": True,
            "image": "gridappsd/gridappsd:{{DEFAULT_GRIDAPPSD_TAG}}",
            "pull": True,
            "ports": {"61613/tcp": 61613, "61614/tcp": 61614, "61616/tcp": 61616},
            "environment": {
                "PATH": "/gridappsd/bin:/gridappsd/lib:/gridappsd/services/fncsgossbridge/service:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin",
                "DEBUG": 1,
                "START": 1
            },
            "links": {"mysql": "mysql",
                      "influxdb": "influxdb",
                      "blazegraph": "blazegraph",
                      "proven": "proven",
                      "redis": "redis"},
            "volumes": {
                str(Path(GRIDAPPSD_CONF_DIR).joinpath("entrypoint.sh")):
                    {"bind": "/gridappsd/entrypoint.sh", "mode": "rw"},
                str(Path(GRIDAPPSD_CONF_DIR).joinpath("run-gridappsd.sh")):
                    {"bind": "/gridappsd/run-gridappsd.sh", "mode": "rw"}
            }
        }
    }

    def __update_template_data__(data, update_dict):
        data_cpy = deepcopy(data)
        for k, v in data_cpy.items():
            for u, p in update_dict.items():
                v['image'] = v['image'].replace(u, p)

        return data_cpy


    __replace_dict__ = {"{{DEFAULT_GRIDAPPSD_TAG}}": DEFAULT_GRIDAPPSD_TAG}
    DEFAULT_DOCKER_DEPENDENCY_CONFIG = __update_template_data__(__TPL_DEPENDENCY_CONFIG__, __replace_dict__)
    DEFAULT_GRIDAPPSD_DOCKER_CONFIG = __update_template_data__(__TPL_GRIDAPPSD_CONFIG__, __replace_dict__)

    def update_gridappsd_tag(new_gridappsd_tag):
        """
        Update the default tag used within the dependency and gridappsd containers to be
        what is specified in the new gridappsd_tag variable
        """
        global DEFAULT_GRIDAPPSD_TAG

        DEFAULT_GRIDAPPSD_TAG = new_gridappsd_tag
        print(f"Updated to using gridappsd tag {DEFAULT_GRIDAPPSD_TAG} ")
        __replace_dict__.update({"{{DEFAULT_GRIDAPPSD_TAG}}": DEFAULT_GRIDAPPSD_TAG})
        DEFAULT_DOCKER_DEPENDENCY_CONFIG.update(__update_template_data__(__TPL_DEPENDENCY_CONFIG__, __replace_dict__))
        DEFAULT_GRIDAPPSD_DOCKER_CONFIG.update(__update_template_data__(__TPL_GRIDAPPSD_CONFIG__, __replace_dict__))


    class Containers:
        """
        This class allows the creation/management of containers created by the gridappsd
        docker process.
        """
        def __init__(self, container_def):
            self._container_def = container_def

        @staticmethod
        def container_list(ignore_list: Optional[Union[str, list]] = "gridappsd_dev"):
            """
            Provides a wrapper around the listing of docker containers.  This function was
            brought about when running from within a docker container.

            Currently the docker container that is run using docker-compose up from the
            gridappsd-dev-environment is specified as gridappsd_dev, however this can change
            and could potentially be extended to multiple named containers.

            @param: ignore_list:
                optional container names to not stop :: A string or list of strings
            """
            client = docker.from_env()

            if ignore_list is None:
                ignore_list = []
            elif isinstance(ignore_list, str):
                ignore_list = [ignore_list]
            containers = []
            for container in client.containers.list():
                if container.name not in ignore_list:
                    containers.append(container)
            return containers

        @staticmethod
        def reset_all_containers(ignore_list: Optional[Union[str, list]] = "gridappsd_dev"):
            """
            Provides a wrapper around the resetting of all docker containers.  This function was
            brought about when running from within a docker container.

            Currently the docker container that is run using docker-compose up from the
            gridappsd-dev-environment is specified as gridappsd_dev, however this can change
            and could potentially be extended to multiple named containers.

            @param: ignore_list:
                optional container names to not stop :: A string or list of strings
            """
            client = docker.from_env()

            if ignore_list is None:
                ignore_list = []
            elif isinstance(ignore_list, str):
                ignore_list = [ignore_list]

            for container in client.containers.list():
                if container.name not in ignore_list:
                    container.kill()

        def check_required_running(self, config):
            my_config = deepcopy(config)
            client = docker.from_env()

            for c in client.containers.list():
                my_config.pop(c.name, None)

            assert not my_config, f"The required containers were not satisfied missing {list(my_config.keys())}"

        def start(self):
            pprint(DEFAULT_GRIDAPPSD_DOCKER_CONFIG)
            client = docker.from_env()
            print(f"Docker client version: {client.version()}")
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
                    if self._container_def[service].get('environment'):
                        kwargs['environment'] = value['environment']
                    if self._container_def[service].get('ports'):
                        kwargs['ports'] = value['ports']
                    if self._container_def[service].get('volumes'):
                        kwargs['volumes'] = value['volumes']
                    if self._container_def[service].get('entrypoint'):
                        kwargs['entrypoint'] = value['entrypoint']
                    if self._container_def[service].get('links'):
                        kwargs['links'] = value['links']
                    for k, v in kwargs.items():
                        print(f"k->{k}, v->{v}")
                    container = client.containers.run(**kwargs)
                    self._container_def[service]['containerid'] = container.id
            print([x.name for x in client.containers.list()])

        def wait_for_log_pattern(self, container, pattern, timeout=30):
            assert self._container_def.get(container), f"Container {container} is not in definition."
            client = docker.from_env()
            container = client.containers.get(self._container_def.get(container)['containerid'])
            until = datetime.now() + timedelta(timeout)
            for p in container.logs(stream=True, until=until):
                print(p)
                if pattern in p.decode('utf-8'):
                    print(f"Found patter {pattern}")
                    return
            raise TimeoutError(f"Pattern {pattern} was not found in logs of container {container} within {timeout}s")

        def wait_for_http_ok(self, url, timeout=30):
            import requests
            results = None
            test_count = 0

            while results is None or not results.ok:
                test_count += 1
                if test_count > timeout:
                    raise TimeoutError(f"Could not reach {url} within alloted timeout {timeout}s")
                results = requests.get(url)
                time.sleep(1)

            print(f"Found url {url} within timeout {timeout}")

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


    threads = []

    def stream_container_log_to_file(container_name: str, logfile: str):
        client = docker.from_env()
        container = client.containers.list(filters=dict(name=container_name))[0]

        print(container)

        def log_output():
            nonlocal container, logfile
            print(f"Starting to write to file {logfile}.")
            with open(logfile, 'wb') as fp:
                print(f"openfile")
                for p in container.logs(stream=True, stderr=PIPE, stdout=PIPE):
                    fp.write(p)
                    fp.flush()

        threading.Thread(target=log_output, daemon=True).start()


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

        containers = Containers(DEFAULT_DOCKER_DEPENDENCY_CONFIG)

        containers.start()
        try:
            yield containers
        finally:
            if stop_after:
                containers.stop()


    @contextlib.contextmanager
    def run_gridappsd_container(stop_after=True):
        """ A contextmanager that uses """

        containers = Containers(DEFAULT_GRIDAPPSD_DOCKER_CONFIG)

        containers.start()
        try:
            containers.wait_for_log_pattern("gridappsd", "MYSQL")
            # Wait for blazegraph to show up
            time.sleep(30)
            containers.wait_for_http_ok("http://localhost:8889/bigdata/", timeout=300)
            # Waith 30 seconds before returning from this to make sure
            # gridappsd container is fully setup ready for simulation
            # and querying.
            yield containers
        finally:
            if stop_after:
                containers.stop()
