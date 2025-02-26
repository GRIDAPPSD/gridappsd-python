import unittest
import subprocess
from gridappsd_field_bus.field_interface.interfaces import MessageBusFactory, MessageBusDefinition, ConnectionType

class TestMessageBusFactory(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Start Artemis Docker container
        subprocess.run(["docker", "run", "-d", "--name", "artemis", "-p", "61616:61616", "-p", "8161:8161", "vromero/activemq-artemis"])

    @classmethod
    def tearDownClass(cls):
        # Stop and remove Artemis Docker container
        subprocess.run(["docker", "stop", "artemis"])
        subprocess.run(["docker", "rm", "artemis"])

    def setUp(self):
        self.factory = MessageBusFactory()
        self.config = MessageBusDefinition(
            id="test_bus",
            connection_type=ConnectionType.CONNECTION_TYPE_GRIDAPPSD,
            connection_args={"GRIDAPPSD_USER": "artemis", "GRIDAPPSD_PASSWORD": "aretemis",
                             "GRIDAPPSD_PORT": 61613, "GRIDAPPSD_ADDRESS": "localhost"}
        )

    def test_create_message_bus(self):
        message_bus = self.factory.create(self.config)
        self.assertIsNotNone(message_bus)
        self.assertEqual(message_bus.id, "test_bus")
        self.assertEqual(message_bus.is_ot_bus, False)

if __name__ == '__main__':
    unittest.main()
