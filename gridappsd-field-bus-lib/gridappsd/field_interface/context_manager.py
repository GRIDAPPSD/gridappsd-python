import argparse
import logging
import os
import time
from typing import Dict

import gridappsd.field_interface.agents.agents as agents_mod
import gridappsd.topics as t
from cimgraph.data_profile import CIM_PROFILE
from gridappsd import GridAPPSD
from gridappsd.field_interface.agents import (FeederAgent, SecondaryAreaAgent,
                                              SwitchAreaAgent)
from gridappsd.field_interface.interfaces import MessageBusDefinition


cim_profile = CIM_PROFILE.RC4_2021.value

agents_mod.set_cim_profile(cim_profile=cim_profile,iec61970_301=7)

cim = agents_mod.cim

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('goss').setLevel(logging.ERROR)
logging.getLogger('stomp.py').setLevel(logging.ERROR)

_log = logging.getLogger(__name__)

#FieldBusManager's request topics. To be used only by context manager user role only.
REQUEST_FIELD = ".".join((t.PROCESS_PREFIX, "request.field"))


class FeederAreaContextManager(FeederAgent):

    def __init__(self,
                 upstream_message_bus_def: MessageBusDefinition,
                 downstream_message_bus_def: MessageBusDefinition,
                 agent_config: Dict,
                 feeder_dict: Dict = None,
                 simulation_id: str = None):

        self.ot_connection = GridAPPSD()
        if feeder_dict is None:
            request = {'request_type':'get_context',
                       'modelId': downstream_message_bus_def.id}
            feeder_dict = None
            while feeder_dict is None:
                self.ot_connection.get_logger().info(f"Requesting topology for {self.__class__}")
                response = self.ot_connection.get_response(REQUEST_FIELD, request, timeout=10)
                if 'data' in response:
                    feeder_dict = response['data']
                    self.ot_connection.send_status("******RCVD FEEDER *************", '/topic/goss.gridappsd.platform.log', 'DEBUG')
                else:
                    time.sleep(5)
        super().__init__(upstream_message_bus_def, downstream_message_bus_def,
                         agent_config, feeder_dict, simulation_id)

        #Override agent_id to a static value
        self.agent_id = downstream_message_bus_def.id + '.context_manager'
        
        self.context = None

        self.registered_agents = {}
        self.registered_agents[self.agent_id] = self.get_registration_details()

        self.neighbouring_agents = {}
        self.upstream_agents = {}
        self.downstream_agents = {}

    def on_request(self, message_bus, headers: Dict, message):

        _log.debug(f"Received request: {message}")

        if message['request_type'] == 'get_context':
            reply_to = headers['reply-to']
            if self.context is None:
                self.context = self.ot_connection.get_response(REQUEST_FIELD, message)
            message_bus.send(reply_to,self.context)

        elif message['request_type'] == 'register_agent':
            self.ot_connection.send(t.REGISTER_AGENT_QUEUE, message)
            self.registered_agents[message['agent']
                                   ['agent_id']] = message['agent']

        elif message['request_type'] == 'get_agents':
            reply_to = headers['reply-to']
            message_bus.send(reply_to, self.registered_agents)

        elif message['request_type'] == 'is_initialized':
            reply_to = headers['reply-to']
            message = {'initialized':True}
            message_bus.send(reply_to, message)

        elif message['request_type'] == 'control_command':
            simulation_id = message['input']['simulation_id']
            self.ot_connection.send(t.simulation_input_topic(simulation_id),
                                    message)


class SwitchAreaContextManager(SwitchAreaAgent):

    def __init__(self,
                 upstream_message_bus_def: MessageBusDefinition,
                 downstream_message_bus_def: MessageBusDefinition,
                 agent_config: Dict,
                 switch_area_dict: Dict = None,
                 simulation_id: str = None):

        self.ot_connection = GridAPPSD()
        if switch_area_dict is None:
            request = {'request_type':'get_context',
                       'areaId': downstream_message_bus_def.id}
            switch_area_dict = self.ot_connection.get_response(
                REQUEST_FIELD, request, timeout=10)['data']

        super().__init__(upstream_message_bus_def, downstream_message_bus_def,
                         agent_config, switch_area_dict, simulation_id)

        #Override agent_id to a static value
        self.agent_id = downstream_message_bus_def.id + '.context_manager'
        
        self.context = None

        self.registered_agents = {}
        self.registered_agents[self.agent_id] = self.get_registration_details()

    def on_request(self, message_bus, headers: Dict, message):

        _log.debug(f"Received request: {message}")

        if message['request_type'] == 'get_context':
            #TODO: check for initialization
            reply_to = headers['reply-to']
            if self.context is None:
                self.context = self.ot_connection.get_response(REQUEST_FIELD, message)
            message_bus.send(reply_to,self.context)

        elif message['request_type'] == 'register_agent':
            #TODO: check for initialization
            self.ot_connection.send(t.REGISTER_AGENT_QUEUE, message)
            self.registered_agents[message['agent']
                                   ['agent_id']] = message['agent']

        elif message['request_type'] == 'get_agents':
            #TODO: check for initialization
            reply_to = headers['reply-to']
            message_bus.send(reply_to, self.registered_agents)
            
        elif message['request_type'] == 'is_initialized':
            reply_to = headers['reply-to']
            message = {'initialized':True}
            message_bus.send(reply_to, message)

        elif message['request_type'] == 'control_command':
            simulation_id = message['input']['simulation_id']
            self.ot_connection.send(t.simulation_input_topic(simulation_id),
                                    message)


class SecondaryAreaContextManager(SecondaryAreaAgent):

    def __init__(self,
                 upstream_message_bus_def: MessageBusDefinition,
                 downstream_message_bus_def: MessageBusDefinition,
                 agent_config: Dict,
                 secondary_area_dict: Dict = None,
                 simulation_id: str = None):

        self.ot_connection = GridAPPSD()
        if secondary_area_dict is None:
            request = {'request_type':'get_context',
                       'areaId': downstream_message_bus_def.id}
            secondary_area_dict = self.ot_connection.get_response(
                REQUEST_FIELD, request, timeout=10)['data']

        super().__init__(upstream_message_bus_def, downstream_message_bus_def,
                         agent_config, secondary_area_dict, simulation_id)

        #Override agent_id to a static value
        self.agent_id = downstream_message_bus_def.id + '.context_manager'
        
        self.context = None

        self.registered_agents = {}
        self.registered_agents[self.agent_id] = self.get_registration_details()

    def on_request(self, message_bus, headers: Dict, message):

        _log.debug(f"Received request: {message}")
        _log.debug(f"Received request: {headers}")

        if message['request_type'] == 'get_context':
            reply_to = headers['reply-to']
            if self.context is None:
                self.context = self.ot_connection.get_response(REQUEST_FIELD, message)
            message_bus.send(reply_to,self.context)


        elif message['request_type'] == 'register_agent':
            self.ot_connection.send(t.REGISTER_AGENT_QUEUE, message)
            self.registered_agents[message['agent']
                                   ['agent_id']] = message['agent']

        elif message['request_type'] == 'get_agents':
            reply_to = headers['reply-to']
            message_bus.send(reply_to, self.registered_agents)

        elif message['request_type'] == 'is_initialized':
            reply_to = headers['reply-to']
            message = {'initialized':True}
            message_bus.send(reply_to, message)

        elif message['request_type'] == 'control_command':
            simulation_id = message['input']['simulation_id']
            self.ot_connection.send(t.simulation_input_topic(simulation_id),
                                    message)

def get_MessageBusDefinition(area_id: str) -> MessageBusDefinition:
    
    connection_args = {"GRIDAPPSD_ADDRESS": os.environ.get('GRIDAPPSD_ADDRESS',"tcp://gridappsd:61613"),
                       "GRIDAPPSD_USER": os.environ.get('GRIDAPPSD_USER'),
                       "GRIDAPPSD_PASSWORD": os.environ.get('GRIDAPPSD_PASSWORD'),
                       "GRIDAPPSD_APPLICATION_ID": os.environ.get('GRIDAPPSD_APPLICATION_ID')}
    
    bus = MessageBusDefinition(id=area_id, 
                               is_ot_bus= True, 
                               connection_type = "GRIDAPPSD_TYPE_GRIDAPPSD",
                               conneciton_args = connection_args)
    
    return bus

def _main():

    time.sleep(10)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--simulation_id",
        help=
        "Simulation id to use for communicating with simulated devices on the message bus. \
                        If simulation_id is not provided then Context Manager assumes to run on deployed field with real devices.",
        required=False)
    opts = parser.parse_args()
    simulation_id = opts.simulation_id

    agent_config = {
        "app_id":
        "context_manager",
        "description":
        "This agent provides topological context information like neighboring agents and devices to other distributed agents"
    }


    gapps = GridAPPSD()
    response = gapps.get_response(t.PLATFORM_STATUS, {"isField":True})
    field_model_mrid = response['fieldModelMrid']

    is_field_initialized = False

    while not is_field_initialized:
        response = gapps.get_response(REQUEST_FIELD, {"request_type":"is_initilized"})
        print(response)
        is_field_initialized = response['data']['initialized']
        time.sleep(1)

    system_message_bus_def = get_MessageBusDefinition(field_model_mrid)
    feeder_message_bus_def = get_MessageBusDefinition(field_model_mrid)

    #TODO: create access control for agents for different layers
    feeder_agent = FeederAreaContextManager(system_message_bus_def,
                                            feeder_message_bus_def,
                                            agent_config,
                                            simulation_id=simulation_id)



    for switch_area in feeder_agent.agent_area_dict['switch_areas']:
        switch_area_message_bus_def = get_MessageBusDefinition(str(switch_area['message_bus_id']))
        print("Creating switch area agent " +
              str(switch_area['message_bus_id']))
        switch_area_agent = SwitchAreaContextManager(
            feeder_message_bus_def,
            switch_area_message_bus_def,
            agent_config,
            simulation_id=simulation_id)
    
        # create secondary area distributed agents
        for secondary_area in switch_area['secondary_areas']:
            secondary_area_message_bus_def = get_MessageBusDefinition(str(secondary_area['message_bus_id']))
            print("Creating secondary area agent " +
                  str(secondary_area['message_bus_id']))
            secondary_area_agent = SecondaryAreaContextManager(
                switch_area_message_bus_def,
                secondary_area_message_bus_def,
                agent_config,
                simulation_id=simulation_id)

    while True:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            print("Exiting sample")
            break


if __name__ == "__main__":
    _main()
