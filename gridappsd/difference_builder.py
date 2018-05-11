from datetime import datetime
from uuid import uuid4

import pytz


class DifferenceBuilder(object):
    """ Automates the building of forward and reverse cim differences

    """

    def __init__(self, simulation_id):

        self._simulation_id = simulation_id
        self._forward = []
        self._reverse = []

    def add_difference(self, object_id, attribute, forward_value, reverse_value):
        """ Add forward and reverse unit for an object attribute.

         All of the parameters must be serializable for sending the GOSS message bus.
         """
        forward = dict(object=object_id, attribute=attribute, value=forward_value)
        reverse = dict(object=object_id, attribute=attribute, value=reverse_value)
        self._forward.append(forward)
        self._reverse.append(reverse)

    def clear(self):
        self._forward = []
        self._reverse = []

    def get_message(self):

        msg = dict(command="update",
                   input=dict(simulation_id=self._simulation_id,
                              message=dict(timestamp=datetime.now(tz=pytz.UTC).isoformat(sep=' '),  #."2018-01-08 13:27:00.000Z",
                                           difference_mrid=uuid4(),
                                           reverse_differences=self._reverse,
                                           forward_differences=self._forward)))
        return msg.copy()
