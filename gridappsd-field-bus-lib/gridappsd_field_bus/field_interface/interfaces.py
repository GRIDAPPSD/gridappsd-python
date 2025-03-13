from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import importlib
import gridappsd.topics as t
import logging
from os import PathLike
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import yaml

_log = logging.getLogger(__name__)


class FieldProtocol(Enum):
    PROTOCOL_2030_5 = "2030.5"
    PROTOCOL_DNP3 = "DNP3"


class SerializationProtocol(Enum):
    JSON = "JSON"
    XML = "XML"


class ConnectionType(Enum):
    # VOLTTRON based connection
    CONNECTION_TYPE_VOLTTRON = "VIP"
    # Web Socket
    # CONNECTION_TYPE_WS = "WS"
    # CONNECTION_TYPE_HTTP = "HTTP"
    # CONNECTION_TYPE_TCP = "TCP"
    CONNECTION_TYPE = "STOMP"
    CONNECTION_TYPE_GRIDAPPSD = "gridappsd_field_bus.field_interface.gridappsd_field_bus.GridAPPSDMessageBus"


class ProtocolTransformer(ABC):

    @staticmethod
    @abstractmethod
    def to_cim(data) -> str:
        """
        Create a cim message based upon the data passed for a given
        concrete protocol.  This is set as a static class because
        all transformers should have this capability.

        This function should return a string that can be manipulated
        to go onto whatever message bus is necessary.
        """
        pass

    @staticmethod
    @abstractmethod
    def to_protocol(cim_data: str, from_format: Optional[str] = None):
        """
        Change passed cim data into a protocol complient data stream
        and return it.

        cim_data: string representing cim data structures/change structure
        from_format: specifies the type
        """
        pass


@dataclass
class MessageBusDefinition:
    """
    A `MessageBusDefinition` class is used to define how to connect to the
    message bus.
    """
    """
    A global unique string representing a specific message bus.
    """
    id: str
    """
    connection_type describes how the agent/endpoint will connect to the message bus
    """
    connection_type: ConnectionType
    """
    connection_args allows dynamic key/value paired strings to be added to allow connections.
    """
    connection_args: Dict[str, str | int]

    """
    Determines whether or not this message bus has the role of ot bus.
    """
    is_ot_bus: bool = False

    @staticmethod
    def __validate_loader__(json_obj: dict[str, Any]) -> bool:
        required = ["id", "connection_type", "connection_args"]
        for k in required:
            if k not in json_obj:
                raise ValueError(f"Missing keys for connection {k}")

        return True

    @staticmethod
    def load_from_json(json_obj: dict[str, str | dict]) -> MessageBusDefinition:
        MessageBusDefinition.__validate_loader__(json_obj)

        mb_def = MessageBusDefinition(**json_obj)
        if not hasattr(mb_def, "is_ot_bus"):
            setattr(mb_def, "is_ot_bus", False)

        return mb_def

    @staticmethod
    def load(config_file) -> MessageBusDefinition:
        """
        Load a single message bus definition from a YAML file.
        """
        config = yaml.load(open(config_file), Loader=yaml.FullLoader)['connections']

        return MessageBusDefinition.load_from_json(config)


class FieldMessageBus:

    def __init__(self, config: MessageBusDefinition):
        self._devices = dict()
        self._is_ot_bus = config.is_ot_bus
        self._id = config.id

    @property
    def id(self):
        return self._id

    @property
    def is_ot_bus(self):
        return self._is_ot_bus

    def add_device(self, device: "DeviceFieldInterface"):
        self._devices[device.id] = device

    def disconnect_device(self, id: str):
        del self._devices[id]

    @abstractmethod
    def query_devices(self) -> dict:
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Is this object connected to the message bus
        """
        pass

    @abstractmethod
    def connect(self):
        """
        Connect to the concrete message bus that implements this interface.
        """
        pass

    @abstractmethod
    def subscribe(self, topic, callback):
        pass

    @abstractmethod
    def unsubscribe(self, topic):
        pass

    @abstractmethod
    def send(self, topic, message):
        """
        Publish device specific message to the concrete message bus.
        """
        pass

    @abstractmethod
    def get_response(self, topic, message, timeout):
        """
        Sends a message on a specific queue, waits and returns the response
        """

    def get_agent_response(self, agent_id, message, timeout):
        """
        Sends a message on a specific agent's request queue, waits and returns the response
        """
        topic = "{}.request.{}.{}".format(t.BASE_FIELD_QUEUE, self.id, agent_id)
        self.get_response(topic, message, timeout)

    @abstractmethod
    def disconnect(self):
        """
        Disconnect the device from the concrete message bus.
        """
        pass


class MessageBusFactory(ABC):
    """
    A factory class for creating message bus objects.
    """

    @staticmethod
    def create(config: MessageBusDefinition) -> FieldMessageBus:
        """
        Create a message bus based upon the configuration passed.
        """
        try:
            module_name, class_name = config.connection_type.value.rsplit('.', 1)
        except AttributeError:
            module_name, class_name = config.connection_type.rsplit('.', 1)

        module = importlib.import_module(module_name)
        bus_class = getattr(module, class_name)
        return bus_class(config)



class MessageBusDefinitions:

    def __init__(
        self,
        config: Optional[Union[dict, str]] = None,
        yamlfile: Optional[Union[str, PathLike]] = None,
    ):
        self._buses = dict()

        if config is None and yamlfile is None:
            raise ValueError("Must have either config specified")

        if config and yamlfile:
            raise ValueError("Must have at least one of config or yamlfile specified.")

        if yamlfile:
            if not Path(yamlfile).exists():
                raise ValueError(f"Invalid path for yamlfile {yamlfile}")
            with open(yamlfile) as fp:
                config = yaml.safe_load(fp)
        elif isinstance(config, str):
            config = yaml.load(config)

        if config.get("connections"):
            for con in config.get("connections"):
                obj = MessageBusDefinition.load(con)
                if self._buses.get(obj.id):
                    raise ValueError(f"Duplicate messagebus id specified for {obj.id}")
                self._buses[obj.id] = obj
        else:
            obj = MessageBusDefinition.load(config)
            self._buses[obj.id] = obj

        self._iterator = None

    def get(self, id: str) -> Union[MessageBusDefinition, None]:
        return self._buses.get(id)

    def __iter__(self):
        if self._iterator is None:
            self._iterator = iter(self._buses)
        return self._iterator

    def __next__(self) -> MessageBusDefinition:
        try:
            definition = next(self._iterator)
        except StopIteration:
            self._iterator = None
            return None
        else:
            return definition


class DeviceFieldInterface:

    def __init__(
        self,
        id: str,
        field_bus: FieldMessageBus,
        publish_topic: str,
        control_topic: str,
    ):
        self._id = id
        self._field_bus = field_bus
        self._publish_topic = publish_topic
        self._control_topic = control_topic
        self._running = False

    @property
    def id(self):
        return self._id

    @property
    def publish_topic(self):
        return self._publish_topic

    @property
    def control_topic(self):
        return self._control_topic

    def publish_field_bus(self, cim_data):
        self._field_bus.publish(topic=self._publish_topic, data=cim_data)

    @abstractmethod
    def on_control_message(self, message):
        pass

    @abstractmethod
    def on_state_change(self):
        """
        This event should be triggered by the device/protocol that
        is used.
        """
        pass
