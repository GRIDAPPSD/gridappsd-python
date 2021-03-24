#!/usr/bin/env python3

import contextlib
import logging
import os
import re
import sys
import shutil
import tarfile
import threading
import time
import urllib.request
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from pprint import pformat
from subprocess import PIPE
from typing import Optional, Union

_log = logging.getLogger("gridappsd.docker_handler")

try:
    import docker
    HAS_DOCKER = True
except ImportError:
    _log.warning("Docker api not loaded. pip install docker to install as package.")
    HAS_DOCKER = False

if HAS_DOCKER:

    # This named container will be used to hold configuration/folders so that other containers
    # that start can use them.  To use add "volume_from": [CONFIGURATION_CONTAINER_NAME] and
    # the mount point within the container will also be within the service container.
    CONFIGURATION_CONTAINER_NAME = "testconfig"

    def expand_all(user_path):
        return os.path.expandvars(os.path.expanduser(user_path))

    # This path needs to be the path to the repo where configuration files are located.
    GRIDAPPSD_CONF_DIR = expand_all(os.environ.get("GRIDAPPSD_CONF_DIR",
                                                   "/home/gridappsd/repos/gridappsd-python/gridappsd/conf"))
                                                   # pkg_resources.resource_filename('gridappsd', 'conf')))
    GRIDAPPSD_ASSET_DIR = "/home/gridappsd/assets"
    os.makedirs(GRIDAPPSD_ASSET_DIR, exist_ok=True)

    GRIDAPPSD_ASSET_CONF_DIR = str(Path(GRIDAPPSD_ASSET_DIR).joinpath("conf"))
    shutil.rmtree(GRIDAPPSD_ASSET_CONF_DIR, ignore_errors=True)
    shutil.copytree(GRIDAPPSD_CONF_DIR, GRIDAPPSD_ASSET_CONF_DIR)
    if not Path(GRIDAPPSD_ASSET_CONF_DIR).is_dir():
        raise AttributeError(f"Couldn't create {GRIDAPPSD_ASSET_CONF_DIR}")

    GRIDAPPSD_DATA_REPO = str(Path(GRIDAPPSD_ASSET_DIR).joinpath("mysql").resolve())

    os.makedirs(GRIDAPPSD_DATA_REPO, exist_ok=True)
    if not Path(GRIDAPPSD_DATA_REPO).is_dir():
        raise AttributeError(f"Invalid GRIDAPPSD_DATA_REPO couldn't make or doesn't exist {GRIDAPPSD_DATA_REPO}")

    assert Path(GRIDAPPSD_ASSET_CONF_DIR).exists()
    assert Path(GRIDAPPSD_ASSET_CONF_DIR).joinpath("entrypoint.sh").exists()
    assert Path(GRIDAPPSD_ASSET_CONF_DIR).joinpath("run-gridappsd.sh").exists()

    MYSQL_SCHEMA_INIT_DIR = f'{GRIDAPPSD_DATA_REPO}/docker-entrypoint-initdb.d'


    def mysql_setup():
        """
        Downloads gridappsd_mysql_dump.sql into the MYSQL_SCHEMA_INIT_DIR init directory.
        This will then be mounted into the mysql container.
        """
        # Downlaod mysql file
        _log.debug("Downloading mysql data file from Bootstrap repository")
        mysql_file = f'{MYSQL_SCHEMA_INIT_DIR}/gridappsd_mysql_dump.sql'
        if os.path.isdir(mysql_file):
            raise RuntimeError(f"mysql datafile is directory, delete {mysql_file} using sudo rm -rf {mysql_file}")
        if not os.path.isdir(MYSQL_SCHEMA_INIT_DIR):
            os.makedirs(MYSQL_SCHEMA_INIT_DIR, 0o0775, exist_ok=True)
        urllib.request.urlretrieve(
            'https://raw.githubusercontent.com/GRIDAPPSD/Bootstrap/master/gridappsd_mysql_dump.sql',
            filename=mysql_file)

        # Modify the mysql file to allow connections from gridappsd container
        with open(mysql_file, "r") as sources:
            lines = sources.readlines()
        with open(mysql_file, "w") as sources:
            for line in lines:
                sources.write(re.sub(r'localhost', '%', line))
        assert Path(mysql_file).exists()

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
            # "volumes": {
            #     "/home/gridappsd/test-assets": {"bind": "/whatthehell", "mode": "rw"}
            #     #"test-assets": {"bind": "/whatthehell", "mode": "rw"}
            #     #data_dir + "/dumps/": {"bind": "/docker-entrypoint-initdb.d/", "mode": "ro"}
            # },
            # Our own so we can create
            "volumes_required": [
                dict(name="mysql_config",
                     local_path=MYSQL_SCHEMA_INIT_DIR,
                     container_path="/docker-entrypoint-initdb.d")
            ],
            "volumes_from": [
                "mysql_config"
            ],
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
            "image": "gridappsd/gridappsd:releases_2020.12.0",
            # "image": "gridappsd/gridappsd:{{DEFAULT_GRIDAPPSD_TAG}}",
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
            "volumes_required": [
                dict(name="gridappsd_config",
                     local_path=GRIDAPPSD_ASSET_CONF_DIR,
                     container_path="/blahblahblah")
            ],
            "volumes_from": [
                "gridappsd_config"
            ],
            "entrypoint": "/startup/entrypoint.sh"
            # "command": "/startup/entrypoint.sh"
            # "volumes": {
            #     "test-assets": dict(
            #         bind="/tmp/test-assets",
            #         mode="rw"
            #     )
            #     # str(Path(GRIDAPPSD_CONF_DIR).joinpath("entrypoint.sh")):
            #     #     {"bind": "/gridappsd/entrypoint.sh", "mode": "rw"},
            #     # str(Path(GRIDAPPSD_CONF_DIR).joinpath("run-gridappsd.sh")):
            #     #     {"bind": "/gridappsd/run-gridappsd.sh", "mode": "rw"}
            # }
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
        _log.info(f"Updated gridappsd docker tag {DEFAULT_GRIDAPPSD_TAG} ")
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

        @staticmethod
        def check_required_running(self, config):
            my_config = deepcopy(config)
            client = docker.from_env()

            for c in client.containers.list():
                my_config.pop(c.name, None)

            assert not my_config, f"The required containers were not satisfied missing {list(my_config.keys())}"

        @staticmethod
        def create_volume_container(name, volume_name,
                                    mount_in_container_at, restart_if_exists: bool = False,
                                    mode="rw"):

            _log.info(f"Creating container {name} and mounting volume {volume_name} "
                      f"at {mount_in_container_at} in container {name}")
            client = docker.from_env()

            should_create = False
            try:
                container = client.containers.get(name)
            except docker.errors.NotFound:
                # start container
                should_create = True
            else:
                if restart_if_exists:
                    should_create = True
                    container.stop()
                else:
                    return container

            if should_create:
                kwargs = {}
                kwargs['image'] = "alpine"
                # Only name the containers if remove is on
                kwargs['remove'] = True
                kwargs['name'] = name
                kwargs['detach'] = True
                kwargs['volumes'] = {
                    volume_name: {"bind": mount_in_container_at, "mode": mode}
                }
                # keep the container running
                kwargs['command'] = "tail -f /dev/null"
                container = client.containers.run(**kwargs)
                _log.info(f"New container for volume created {container.name}")
                # print(f"New container is: {container.name}")
                return container

        @staticmethod
        def copy_to(src, dst):
            _log.debug(f"copying folder from: {src} to {dst}")
            src = str(src)
            # python3.6 can't combine PosixPath and str
            assert os.path.exists(src), f"{src} does not exist!"
            client = docker.from_env()
            name, dst = dst.split(':')
            container = client.containers.get(name)
            assert container is not None
            cwd = os.getcwd()
            os.chdir(os.path.dirname(src))
            srcname = os.path.basename(src)
            tarfilename = src + '.tar'
            tar = tarfile.open(tarfilename, mode='w')
            try:
                tar.add(srcname)
            finally:
                tar.close()

            data = open(tarfilename, 'rb').read()
            resp = container.put_archive(os.path.dirname(dst), data)
            os.chdir(cwd)
            _log.debug(f"Response from put_archive {resp}")

        def start(self):
            _log.info("Starting containers")
            # Containers.create_volume_container(CONFIGURATION_CONTAINER_NAME, "testconfig", "/testconfig")
            #pprint(DEFAULT_GRIDAPPSD_DOCKER_CONFIG)
            client = docker.from_env()
            # print(f"Docker client version: {client.version()}")
            for service, value in self._container_def.items():
                if self._container_def[service]['pull']:
                    _log.info(f"Pulling {service} : {self._container_def[service]['image']}")
                    client.images.pull(self._container_def[service]['image'])
                # Provide a way to dynamically create things that the container will need
                # on the host system.  This is important if we want to create a volume before
                # starting the container up.
                if value.get('onsetupfn'):
                    value.get('onsetupfn')()

                if self._container_def[service].get("volumes_required"):
                    for vr in self._container_def[service].get("volumes_required"):
                        _log.info(f"Creating volume for {service}: name={vr['name']}, "
                                  f"volume_name={vr['name']}, container_path={vr['container_path']}")
                        container = Containers.create_volume_container(
                            name=vr["name"],
                            volume_name=vr["name"],
                            mount_in_container_at=vr["container_path"]
                            )
                        time.sleep(20)
                        if vr.get("local_path"):
                            _log.debug(f"contents of local path({vr.get('local_path')}):\n\t{os.listdir(vr.get('local_path'))}")
                            _log.info(f"Copy to mounted volume for {service}: "
                                      f"local_path={vr['local_path']}, container_path={vr['container_path']}")
                            resp = Containers.copy_to(vr["local_path"], f'{vr["name"]}:{vr["container_path"]}')
                            _log.info(f"Response from copy_to: {resp} ")

            for service, value in self._container_def.items():
                if self._container_def[service]['start']:
                    _log.debug(f"Starting {service} : {self._container_def[service]['image']}")
                    kwargs = {}
                    kwargs['image'] = self._container_def[service]['image']
                    # Only name the containers if remove is on
                    kwargs['remove'] = True
                    kwargs['name'] = service
                    kwargs['detach'] = True
                    kwargs['entrypoint'] = value.get('entrypoint')
                    if self._container_def[service].get('entrypoint'):
                        kwargs['entrypoint'] = value['entrypoint']
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
                    if self._container_def[service].get('volumes_from'):
                        kwargs['volumes_from'] = value['volumes_from']
                    #for k, v in kwargs.items():
                    #    print(f"k->{k}, v->{v}")
                    _log.debug("Starting container with the following args:")
                    _log.debug(f"{pformat(kwargs)}")
                    container = client.containers.run(**kwargs)
                    # time.sleep(10)
                    # [print(x.name, x.attrs) for x in client.volumes.list()]
                    self._container_def[service]['containerid'] = container.id
            _log.debug(f"Current containers are: {[x.name for x in client.containers.list()]}")

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

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)
    logging.getLogger("docker.utils.config").setLevel(logging.INFO)
    logging.getLogger("docker.auth").setLevel(logging.INFO)
    Containers.reset_all_containers()
    with run_dependency_containers() as container:

        with run_gridappsd_container(stop_after=False):
            pass