# import logging
# from unittest import TestCase
#
# # the following can decorate TestCase or specific test methods
# #@pytest.mark.usefixtures("foo")
# class TemplateTestCase(TestCase):
#
#     @classmethod
#     def setUpClass(cls) -> None:
#         logging.basicConfig(level=logging.DEBUG)
#         logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)
#         logging.getLogger("docker.utils.config").setLevel(logging.INFO)
#         logging.getLogger("docker.auth").setLevel(logging.INFO)
#
#         cls.log = logging.getLogger("test_containers")
#         cls.log.debug("setUpClass")
#
#     def setUp(self) -> None:
#         self.log.debug("Setup")
#
#     def test_can_create_volume(self):
#         assert True
#
#     def test_can_copy_dir(self):
#         assert not True
#
#     def tearDown(self) -> None:
#         self.log.debug("tearDown")
#
#     @classmethod
#     def tearDownClass(cls) -> None:
#         cls.log.debug("tearDownClass")
