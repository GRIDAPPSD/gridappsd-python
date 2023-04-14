from gridappsd.field_interface.interfaces import FieldMessageBus
import dataclasses
import gridappsd.topics as t
import json



class LocalContext:
    
    @classmethod
    def get_context_by_feeder(cls, downstream_message_bus: FieldMessageBus, feeder_mrid, area_id=None):
        
        request = {'request_type' : 'get_context',
                    'modelId': feeder_mrid,
                   'areaId': area_id}
        response = downstream_message_bus.get_response(t.context_request_queue(downstream_message_bus.id), request, timeout=10)
        return response

    @classmethod
    def get_context_by_message_bus(cls, downstream_message_bus: FieldMessageBus):
        """
        return agents/devices based on downstream message bus as input

        """
        request = {'request_type' : 'get_context',
                   'downstream_message_bus_id': downstream_message_bus.id
                   }
        return downstream_message_bus.get_response(t.context_request_queue(downstream_message_bus.id), request)
    
    @classmethod
    def register_agent(cls, downstream_message_bus: FieldMessageBus, upstream_message_bus: FieldMessageBus, agent):
        """
        Sends the newly created distributed agent's info to OT bus

        """
        request = {'request_type' : 'register_agent',
                   'agent' : agent.get_registration_details()}
        downstream_message_bus.send(t.context_request_queue(downstream_message_bus.id), request)
        upstream_message_bus.send(t.context_request_queue(upstream_message_bus.id), request)
    
    @classmethod
    def get_agents(cls, downstream_message_bus: FieldMessageBus):
        """
        Sends the newly created distributed agent's info to OT bus

        """
        request = {'request_type' : 'get_agents'}
        return downstream_message_bus.get_response(t.context_request_queue(downstream_message_bus.id), request)

# Provide context based on router (ip trace) or PKI
# Maybe able to emulate/simulate
