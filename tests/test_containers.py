import logging
import os
from pathlib import Path
import shutil
import sys
from unittest import TestCase

_log = logging.getLogger("test_containers")

try:
    import docker
    HAS_DOCKER = True
except ImportError:
    _log.warning("Docker api not loaded. pip install docker to install as package.")
    HAS_DOCKER = False

from gridappsd.docker_handler import Containers


class ContainersTestCase(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        logging.basicConfig(level=logging.DEBUG,stream=sys.stdout)
        logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)
        logging.getLogger("docker.utils.config").setLevel(logging.INFO)
        logging.getLogger("docker.auth").setLevel(logging.INFO)
        cls.log = logging.getLogger("test_containers")

        cls.tmp_dir = Path("tmpdir")
        os.makedirs(cls.tmp_dir, exist_ok=True)
        cls.tmp_file_name = cls.tmp_dir.joinpath("woot.txt")
        cls.tmp_file_content = """
        here I come to save the day!
"""
        with open(cls.tmp_file_name, "w") as stream:
            stream.write(cls.tmp_file_content)

    def setUp(self) -> None:
        self.cname = "test_container"
        self.vname = "test_volume"
        self.in_container_path = "/foo/bar/bim"
        self.client = docker.from_env()

    def test_can_create_volume(self):
        # container_path = "/foo/bar/bim"
        container = Containers.create_volume_container(name=self.cname,
                                                       volume_name=self.vname,
                                                       mount_in_container_at=self.in_container_path)
        assert self.cname == container.name
        exit_code, result = container.exec_run(cmd=f"ls -la {self.in_container_path}")
        self.log.debug(f"Exit code: {exit_code}, result: {result}")
        assert exit_code == 0

    def test_can_copy_dir(self):
        Containers.create_volume_container(name=self.cname,
                                           volume_name=self.vname,
                                           mount_in_container_at=self.in_container_path)

        Containers.copy_to(str(Path(__file__).parent.joinpath("tmpdir")), f"{self.cname}:/foo/bar/bim/tmpdir")

        container = self.client.containers.get(self.cname)

        exit_code, result = container.exec_run(cmd=f"ls -la {self.in_container_path}")

        assert exit_code == 0
        assert b"tmpdir" in result
        exit_code, result = container.exec_run(cmd=f"ls -la {self.in_container_path}/tmpdir")
        assert exit_code == 0
        assert b"woot.txt" in result

    def tearDown(self) -> None:
        container = self.client.containers.get(self.cname)
        container.stop()
        volume = self.client.volumes.get(self.vname)
        volume.remove()
        self.log.debug("tearDown")

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)
        cls.log.debug("tearDownClass")
