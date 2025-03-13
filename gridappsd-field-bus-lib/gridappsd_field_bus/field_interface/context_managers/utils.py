import os

import gridappsd.topics as t
from gridappsd_field_bus.field_interface.interfaces import MessageBusDefinition, ConnectionType

#FieldBusManager's request topics. To be used only by context manager user role only.
REQUEST_FIELD = ".".join((t.PROCESS_PREFIX, "request.field"))

def get_message_bus_definition(area_id: str) -> MessageBusDefinition:

    connection_args = {
        "GRIDAPPSD_ADDRESS": os.environ.get('GRIDAPPSD_ADDRESS', "tcp://gridappsd:61613"),
        "GRIDAPPSD_USER": os.environ.get('GRIDAPPSD_USER'),
        "GRIDAPPSD_PASSWORD": os.environ.get('GRIDAPPSD_PASSWORD'),
        "GRIDAPPSD_APPLICATION_ID": os.environ.get('GRIDAPPSD_APPLICATION_ID')
    }

    bus = MessageBusDefinition(id=area_id,
                               is_ot_bus=True,
                               connection_type=ConnectionType.CONNECTION_TYPE_GRIDAPPSD,
                               connection_args=connection_args)

    return bus
