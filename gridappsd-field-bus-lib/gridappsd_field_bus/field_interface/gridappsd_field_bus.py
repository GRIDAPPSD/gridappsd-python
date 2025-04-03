import urllib

from loguru import logger as _log

from gridappsd import GridAPPSD
from gridappsd_field_bus.field_interface.interfaces import FieldMessageBus
from gridappsd_field_bus.field_interface.interfaces import MessageBusDefinition
from typing import Any


class GridAPPSDMessageBus(FieldMessageBus):

    def __init__(self, definition: MessageBusDefinition):
        super().__init__(definition)
        self._id = definition.id

        self._user = definition.connection_args["GRIDAPPSD_USER"]
        self._password = definition.connection_args["GRIDAPPSD_PASSWORD"]
        self._address = definition.connection_args["GRIDAPPSD_ADDRESS"]

        self.gridappsd_obj = None

    def query_devices(self) -> dict:
        pass

    def is_connected(self) -> bool:
        """
        Is this object connected to the message bus
        """
        if self.gridappsd_obj is not None:
            return self.gridappsd_obj.connected
        else:
            _log.error("GridAPPSD object is not initialized. Cannot check connection status.")
            return False

    def connect(self):
        """
        Connect to the concrete message bus that implements this interface.
        """
        _log.debug(f"Connecting to GridAPPSD message bus with address: {self._address}")
        if self.gridappsd_obj is None:
            addr = self._address
            if not addr.startswith("tcp://"):
                addr = "tcp://" + self._address
            parsed = urllib.parse.urlparse(addr)
            # TODO Handle a non-auth token field connection if possible 
            self.gridappsd_obj = GridAPPSD(stomp_address=parsed.hostname, stomp_port=parsed.port,
                                            username=self._user,
                                            password=self._password,
                                            use_auth_token=False)
        else:
            _log.error("GridAPPSD object is not initialized. Cannot connect to message bus.")
        

    def subscribe(self, topic, callback):
        _log.debug(f"Subscribing to topic: {topic}")
        if self.gridappsd_obj is not None:
            self.gridappsd_obj.subscribe(topic, callback)
        else:
            _log.error("GridAPPSD object is not connected. Cannot subscribe to topic.")

    def unsubscribe(self, topic):
        pass

    def send(self, topic: str, message: Any):
        """
        Publish device specific data to the concrete message bus.
        """
        _log.debug(f"Sending message to topic: {topic} with message: {message}")
        if self.gridappsd_obj is not None:
            self.gridappsd_obj.send(topic, message)
        else:
            _log.error("GridAPPSD object is not connected. Cannot send message.")

    def get_response(self, topic, message, timeout=5):
        """
        Sends a message on a specific concrete queue, waits and returns the response
        """
        if self.gridappsd_obj is not None:
            return self.gridappsd_obj.get_response(topic, message, timeout)

    def disconnect(self):
        """
        Disconnect from the concrete message bus.
        """
        self.gridappsd_obj.disconnect()
