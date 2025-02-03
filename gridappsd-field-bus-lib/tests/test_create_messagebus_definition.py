import unittest
from unittest.mock import patch, mock_open, MagicMock

import yaml

from gridappsd_field_bus.field_interface.interfaces import FieldMessageBus, MessageBusDefinition, MessageBusDefinitions

class MockDeviceFieldInterface:
    pass

class TestFieldMessageBus(unittest.TestCase):

    def setUp(self):
        self.message_bus_definition = MessageBusDefinition(id="test_id", connection_type="test_type", connection_args={"arg1": "value1"})
        self.field_message_bus = FieldMessageBus(config=self.message_bus_definition)

    def test_id(self):
        self.assertEqual(self.field_message_bus.id, "test_id")

    def test_is_ot_bus(self):
        self.assertFalse(self.field_message_bus.is_ot_bus)

    def test_add_device(self):
        device = MockDeviceFieldInterface()
        self.field_message_bus.add_device = MagicMock()
        self.field_message_bus.add_device(device)
        self.field_message_bus.add_device.assert_called_with(device)

    def test_disconnect_device(self):
        device = MockDeviceFieldInterface()
        self.field_message_bus.add_device = MagicMock()
        self.field_message_bus.disconnect_device = MagicMock()
        self.field_message_bus.add_device(device)
        self.field_message_bus.disconnect_device(device)
        self.field_message_bus.disconnect_device.assert_called_with(device)

class TestMessageBusDefinitionSingle(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data="""
connections:
  id: test_id
  connection_type: test_type
  connection_args:
    arg1: value1
    arg2: value2
""")
    @patch("yaml.load")
    def test_load_message_bus_definition(self, mock_yaml_load, mock_file):
        mock_yaml_load.return_value = {
            'connections': {
                'id': 'test_id',
                'connection_type': 'test_type',
                'connection_args': {
                    'arg1': 'value1',
                    'arg2': 'value2'
                }
            }
        }

        config_file = "dummy_path.yaml"
        config = yaml.load(open(config_file), Loader=yaml.FullLoader)['connections']

        required = ["id", "connection_type", "connection_args"]
        for k in required:
            if k not in config:
                raise ValueError(f"Missing keys for connection {k}")

        definition = MessageBusDefinition(config[required[0]], config[required[1]], config[required[2]])
        for k in config:
            if k == "connection_args":
                definition.connection_args = dict()
                for k1, v1 in config[k].items():
                    definition.connection_args[k1] = v1
            else:
                setattr(definition, k, config[k])

        if not hasattr(definition, "is_ot_bus"):
            setattr(definition, "is_ot_bus", False)

        self.assertEqual(definition.id, "test_id")
        self.assertEqual(definition.connection_type, "test_type")
        self.assertEqual(definition.connection_args, {"arg1": "value1", "arg2": "value2"})
        self.assertFalse(definition.is_ot_bus)

class TestMessageBusDefinition(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data="""
connections:
  - id: test_id_1
    connection_type: test_type_1
    connection_args:
      arg1: value1
      arg2: value2
  - id: test_id_2
    connection_type: test_type_2
    connection_args:
      arg3: value3
      arg4: value4
""")
    @patch("yaml.load")
    def test_load_message_bus_definition_multiple_connections(self, mock_yaml_load, mock_file):
        mock_yaml_load.return_value = {
            'connections': [
                {
                    'id': 'test_id_1',
                    'connection_type': 'test_type_1',
                    'connection_args': {
                        'arg1': 'value1',
                        'arg2': 'value2'
                    }
                },
                {
                    'id': 'test_id_2',
                    'connection_type': 'test_type_2',
                    'connection_args': {
                        'arg3': 'value3',
                        'arg4': 'value4'
                    }
                }
            ]
        }

        config_file = "dummy_path.yaml"
        configs = yaml.load(open(config_file), Loader=yaml.FullLoader)['connections']

        for config in configs:
            required = ["id", "connection_type", "connection_args"]
            for k in required:
                if k not in config:
                    raise ValueError(f"Missing keys for connection {k}")

            definition = MessageBusDefinition(config[required[0]], config[required[1]], config[required[2]])
            for k in config:
                if k == "connection_args":
                    definition.connection_args = dict()
                    for k1, v1 in config[k].items():
                        definition.connection_args[k1] = v1
                else:
                    setattr(definition, k, config[k])

            if not hasattr(definition, "is_ot_bus"):
                setattr(definition, "is_ot_bus", False)

            if definition.id == "test_id_1":
                self.assertEqual(definition.id, "test_id_1")
                self.assertEqual(definition.connection_type, "test_type_1")
                self.assertEqual(definition.connection_args, {"arg1": "value1", "arg2": "value2"})
                self.assertFalse(definition.is_ot_bus)
            elif definition.id == "test_id_2":
                self.assertEqual(definition.id, "test_id_2")
                self.assertEqual(definition.connection_type, "test_type_2")
                self.assertEqual(definition.connection_args, {"arg3": "value3", "arg4": "value4"})
                self.assertFalse(definition.is_ot_bus)

if __name__ == '__main__':
    unittest.main()