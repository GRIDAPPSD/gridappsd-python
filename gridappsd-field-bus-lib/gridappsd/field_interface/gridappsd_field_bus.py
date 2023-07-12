from gridappsd import GridAPPSD
from gridappsd.field_interface.interfaces import FieldMessageBus
from gridappsd.field_interface.interfaces import MessageBusDefinition
from typing import Any


class GridAPPSDMessageBus(FieldMessageBus):
    def __init__(self, definition: MessageBusDefinition):
        super(GridAPPSDMessageBus, self).__init__(definition)
        self._id = definition.id

        self._user = definition.conneciton_args["GRIDAPPSD_USER"]
        self._password = definition.conneciton_args["GRIDAPPSD_PASSWORD"]
        self._address = definition.conneciton_args["GRIDAPPSD_ADDRESS"]

        self.gridappsd_obj = None
        
    def query_devices(self) -> dict:
        pass

    def is_connected(self) -> bool:
        """
        Is this object connected to the message bus
        """
        pass

    def connect(self):
        """
        Connect to the concrete message bus that implements this interface.
        """
        self.gridappsd_obj = GridAPPSD()

    def subscribe(self, topic, callback):
        if self.gridappsd_obj is not None:
            self.gridappsd_obj.subscribe(topic, callback)

    def unsubscribe(self, topic):
        pass

    def send(self, topic: str, message: Any):
        """
        Publish device specific data to the concrete message bus.
        """
        if self.gridappsd_obj is not None:
            self.gridappsd_obj.send(topic, message)
            
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
