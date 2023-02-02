from gridappsd import GridAPPSD

request_field_queue_prefix = 'goss.gridappsd.process.request.field'
request_field_context_queue = request_field_queue_prefix + '.context'


class ContextManager:

    @classmethod
    def get_context_by_feeder(cls, feeder_mrid, area_id=None):
        gridappsd_obj = GridAPPSD()

        request = {'modelId': feeder_mrid,
                   'areaId': area_id}

        response = gridappsd_obj.get_response(request_field_context_queue, request)
        return response

    @classmethod
    def get_context_by_message_bus(cls, downstream_message_bus_id):
        """
        return agents/devices based on upstream and/or downstream message bus as input
        make message bus id a list
        
        based on filter return distributed agents for different applications as well 
        """
        gridappsd_obj = GridAPPSD()

        request = {'downstream_message_bus_id': downstream_message_bus_id,
                   'agents': True,
                   'devices': True}

        return gridappsd_obj.get_response(request_field_context_queue, request)

# Provide context based on router (ip trace) or PKI
# Maybe able to emulate/simulate
