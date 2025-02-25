import logging
import time
from typing import Dict

import gridappsd.topics as t
from gridappsd import GridAPPSD
from gridappsd_field_bus.field_interface.agents import (SubstationAgent, FeederAgent, SecondaryAreaAgent, SwitchAreaAgent)
from gridappsd_field_bus.field_interface.interfaces import MessageBusDefinition
from gridappsd_field_bus.field_interface.context_managers.utils import REQUEST_FIELD

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('goss').setLevel(logging.ERROR)
logging.getLogger('stomp.py').setLevel(logging.ERROR)

_log = logging.getLogger(__name__)

class SubstationAreaContextManager(SubstationAgent):

    def __init__(self,
                 upstream_message_bus_def: MessageBusDefinition,
                 downstream_message_bus_def: MessageBusDefinition,
                 agent_config: Dict,
                 substation_dict: Dict = None,
                 simulation_id: str = None):

        self.ot_connection = GridAPPSD()
        if substation_dict is None:
            request = {'request_type': 'get_context', 'areaId': downstream_message_bus_def.id}
            substation_dict = None
            while substation_dict is None:
                self.ot_connection.get_logger().debug(f"Requesting topology for {self.__class__}")
                response = self.ot_connection.get_response(REQUEST_FIELD, request, timeout=10)
                if 'DistributionArea' in response:
                    substation_dict = response['DistributionArea']['Substation']['@id']
                    self.ot_connection.get_logger().debug("Topology received at Substation Area Context Manager")
                else:
                    time.sleep(5)
        super().__init__(upstream_message_bus_def, downstream_message_bus_def, agent_config,
                         substation_dict, simulation_id)

        #Override agent_id to a static value
        self.agent_id = downstream_message_bus_def.id + '.context_manager'

        self.context = {'data':substation_dict}

        self.registered_agents = {}
        self.registered_agents[self.agent_id] = self.get_registration_details()

        self.neighbouring_agents = {}
        self.upstream_agents = {}
        self.downstream_agents = {}
        self.ot_connection.get_logger().info("Substation Area Context Manager Created")


class FeederAreaContextManager(FeederAgent):

    def __init__(self,
                 upstream_message_bus_def: MessageBusDefinition,
                 downstream_message_bus_def: MessageBusDefinition,
                 agent_config: Dict,
                 feeder_dict: Dict = None,
                 simulation_id: str = None):

        self.ot_connection = GridAPPSD()
        if feeder_dict is None:
            request = {'request_type': 'get_context', 'areaId': downstream_message_bus_def.id}
            feeder_dict = None
            while feeder_dict is None:
                self.ot_connection.get_logger().debug(f"Requesting topology for {self.__class__}")
                response = self.ot_connection.get_response(REQUEST_FIELD, request, timeout=10)
                if 'data' in response:
                    feeder_dict = response['data']
                    self.ot_connection.get_logger().debug("Topology received at Feeder Area Context Manager")
                else:
                    time.sleep(5)
        super().__init__(upstream_message_bus_def, downstream_message_bus_def, agent_config,
                         feeder_dict, simulation_id)

        #Override agent_id to a static value
        self.agent_id = downstream_message_bus_def.id + '.context_manager'

        self.context = {'data':feeder_dict}

        self.registered_agents = {}
        self.registered_agents[self.agent_id] = self.get_registration_details()

        self.neighbouring_agents = {}
        self.upstream_agents = {}
        self.downstream_agents = {}
        self.ot_connection.get_logger().info("Feeder Area Context Manager Created")

    def on_request(self, message_bus, headers: Dict, message):

        _log.debug(f"Received request: {message}")

        if message['request_type'] == 'get_context':
            reply_to = headers['reply-to']
            if self.context is None:
                self.context = self.ot_connection.get_response(REQUEST_FIELD, message)
            message_bus.send(reply_to, self.context)

        elif message['request_type'] == 'register_agent':
            self.ot_connection.send(t.REGISTER_AGENT_QUEUE, message)
            self.registered_agents[message['agent']['agent_id']] = message['agent']

        elif message['request_type'] == 'get_agents':
            reply_to = headers['reply-to']
            message_bus.send(reply_to, self.registered_agents)

        elif message['request_type'] == 'is_initialized':
            reply_to = headers['reply-to']
            message = {'initialized': True}
            message_bus.send(reply_to, message)

        elif message['request_type'] == 'control_command':
            simulation_id = message['input']['simulation_id']
            self.ot_connection.send(t.simulation_input_topic(simulation_id), message)


class SwitchAreaContextManager(SwitchAreaAgent):

    def __init__(self,
                 upstream_message_bus_def: MessageBusDefinition,
                 downstream_message_bus_def: MessageBusDefinition,
                 agent_config: Dict,
                 switch_area_dict: Dict = None,
                 simulation_id: str = None):

        self.ot_connection = GridAPPSD()
        if switch_area_dict is None:
            request = {'request_type': 'get_context', 'areaId': downstream_message_bus_def.id}
            switch_area_dict = self.ot_connection.get_response(REQUEST_FIELD, request,
                                                               timeout=10)['data']

        super().__init__(upstream_message_bus_def, downstream_message_bus_def, agent_config,
                         switch_area_dict, simulation_id)

        #Override agent_id to a static value
        self.agent_id = downstream_message_bus_def.id + '.context_manager'

        self.context = {'data':switch_area_dict}

        self.registered_agents = {}
        self.registered_agents[self.agent_id] = self.get_registration_details()
        self.ot_connection.get_logger().info("Switch Area "+self.agent_id+" Context Manager Created")

    def on_request(self, message_bus, headers: Dict, message):

        _log.debug(f"Received request: {message}")

        if message['request_type'] == 'get_context':
            #TODO: check for initialization
            reply_to = headers['reply-to']
            if self.context is None:
                self.context = self.ot_connection.get_response(REQUEST_FIELD, message)
            message_bus.send(reply_to, self.context)

        elif message['request_type'] == 'register_agent':
            #TODO: check for initialization
            self.ot_connection.send(t.REGISTER_AGENT_QUEUE, message)
            self.registered_agents[message['agent']['agent_id']] = message['agent']

        elif message['request_type'] == 'get_agents':
            #TODO: check for initialization
            reply_to = headers['reply-to']
            message_bus.send(reply_to, self.registered_agents)

        elif message['request_type'] == 'is_initialized':
            reply_to = headers['reply-to']
            message = {'initialized': True}
            message_bus.send(reply_to, message)

        elif message['request_type'] == 'control_command':
            simulation_id = message['input']['simulation_id']
            self.ot_connection.send(t.simulation_input_topic(simulation_id), message)


class SecondaryAreaContextManager(SecondaryAreaAgent):

    def __init__(self,
                 upstream_message_bus_def: MessageBusDefinition,
                 downstream_message_bus_def: MessageBusDefinition,
                 agent_config: Dict,
                 secondary_area_dict: Dict = None,
                 simulation_id: str = None):

        self.ot_connection = GridAPPSD()
        if secondary_area_dict is None:
            request = {'request_type': 'get_context', 'areaId': downstream_message_bus_def.id}
            secondary_area_dict = self.ot_connection.get_response(REQUEST_FIELD,
                                                                  request,
                                                                  timeout=10)['data']

        super().__init__(upstream_message_bus_def, downstream_message_bus_def, agent_config,
                         secondary_area_dict, simulation_id)

        #Override agent_id to a static value
        self.agent_id = downstream_message_bus_def.id + '.context_manager'

        self.context = {'data':secondary_area_dict}

        self.registered_agents = {}
        self.registered_agents[self.agent_id] = self.get_registration_details()
        self.ot_connection.get_logger().info("Secondary Area "+self.agent_id+" Context Manager Created")

    def on_request(self, message_bus, headers: Dict, message):

        _log.debug(f"Received request: {message}")
        _log.debug(f"Received request: {headers}")

        if message['request_type'] == 'get_context':
            reply_to = headers['reply-to']
            if self.context is None:
                self.context = self.ot_connection.get_response(REQUEST_FIELD, message)
            message_bus.send(reply_to, self.context)

        elif message['request_type'] == 'register_agent':
            self.ot_connection.send(t.REGISTER_AGENT_QUEUE, message)
            self.registered_agents[message['agent']['agent_id']] = message['agent']

        elif message['request_type'] == 'get_agents':
            reply_to = headers['reply-to']
            message_bus.send(reply_to, self.registered_agents)

        elif message['request_type'] == 'is_initialized':
            reply_to = headers['reply-to']
            message = {'initialized': True}
            message_bus.send(reply_to, message)

        elif message['request_type'] == 'control_command':
            simulation_id = message['input']['simulation_id']
            self.ot_connection.send(t.simulation_input_topic(simulation_id), message)
