from gridappsd.field_interface.interfaces import MessageBusDefinition
from gridappsd.field_interface.interfaces import FeederMessageBus
from gridappsd import GridAPPSD


class GridAPPSDMessageBus(FeederMessageBus):
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

    def publish(self, data, topic: str = None):
        """
        Publish device specific data to the concrete message bus.
        """
        pass

    def disconnect(self):
        """
        Disconnect the device from the concrete message bus.
        """
        pass
