from dataclasses import dataclass, field
import importlib
import logging
from typing import Dict
import uuid

from cimlab.loaders import ConnectionParameters
from cimlab.loaders import gridappsd
from cimlab.loaders.gridappsd import GridappsdConnection
from cimlab.models import SwitchArea, SecondaryArea, DistributedModel

from gridappsd.field_interface.context import LocalContext
from gridappsd.field_interface.gridappsd_field_bus import GridAPPSDMessageBus
from gridappsd.field_interface.interfaces import MessageBusDefinition
import gridappsd.topics as t 


cim = None
sparql = None


_log = logging.getLogger(__name__)

def set_cim_profile(cim_profile):
    global cim
    cim = importlib.import_module('cimlab.data_profile.' + cim_profile)
    gridappsd.set_cim_profile(cim_profile)

      
class DistributedAgent:


    def __init__(self,
                 upstream_message_bus_def: MessageBusDefinition,
                 downstream_message_bus_def: MessageBusDefinition,
                 agent_config,
                 agent_area_dict=None,
                 simulation_id=None,
                 cim_profile: str = None):
        """
        Creates a DistributedAgent object that connects to the specified message
        buses and gets context based on feeder id and area id.
        """
        _log.debug(f"Creating DistributedAgent: {self.__class__.__name__}")
        self.upstream_message_bus = None
        self.downstream_message_bus = None
        self.simulation_id = simulation_id
        self.context = None
        
        #TODO: Change params and connection to local connection 
        self.params = ConnectionParameters()
        self.connection = GridappsdConnection(self.params)
        
        self.app_id = agent_config['app_id']
        self.description = agent_config['description']
        self.agent_id = str(uuid.uuid4())
        self.agent_area_dict = agent_area_dict
        

        if upstream_message_bus_def is not None:
            if upstream_message_bus_def.is_ot_bus:
                self.upstream_message_bus = GridAPPSDMessageBus(upstream_message_bus_def)
        #            else:
        #                self.upstream_message_bus = VolttronMessageBus(upstream_message_bus_def)

        if downstream_message_bus_def is not None:
            if downstream_message_bus_def.is_ot_bus:
                self.downstream_message_bus = GridAPPSDMessageBus(downstream_message_bus_def)
        #            else:
        #                self.downstream_message_bus = VolttronMessageBus(downstream_message_bus_def)

        # self.context = ContextManager.get(self.feeder_id, self.area_id)

        #if agent_dict is not None:
        #    self.addressable_equipments = agent_dict['addressable_equipment']
        #    self.unaddressable_equipments = agent_dict['unaddressable_equipment']

    def connect(self):
        
        if self.agent_area_dict is None:
            context = LocalContext.get_context_by_message_bus(self.downstream_message_bus)
            self.agent_area_dict = context['data']
            
        if self.upstream_message_bus is not None:
            self.upstream_message_bus.connect()
        if self.downstream_message_bus is not None:
            self.downstream_message_bus.connect()
        if self.downstream_message_bus is None and self.upstream_message_bus is None:
            raise ValueError("Either upstream or downstream bus must be specified!")
        
        self.subscribe_to_measurement()
        self.subscribe_to_messages()
        self.subscribe_to_requests()
        
        if('context_manager' not in self.app_id):
            LocalContext.register_agent(self.downstream_message_bus, self.upstream_message_bus,self)

    def subscribe_to_measurement(self):
        if self.simulation_id is None:
            self.downstream_message_bus.subscribe(f"/topic/goss.gridappsd.field.output.{self.downstream_message_bus.id}", self.on_measurement)
        else:
            topic = f"/topic/goss.gridappsd.field.simulation.output.{self.simulation_id}.{self.downstream_message_bus.id}"
            _log.debug(f"subscribing to simulation output on topic {topic}")
            self.downstream_message_bus.subscribe(topic,
                                                  self.on_simulation_output)
            
    def subscribe_to_messages(self):
        
        
        self.downstream_message_bus.subscribe(t.field_message_bus_topic(self.downstream_message_bus), self.on_downstream_message)
        self.downstream_message_bus.subscribe(t.field_message_bus_topic(self.upstream_message_bus), self.on_upstream_message)
        
        _log.debug(f"Subscribing to messages on application topics: \n {t.field_message_bus_app_topic(self.downstream_message_bus.id, self.app_id)} \
                                                                    \n {t.field_message_bus_app_topic(self.upstream_message_bus.id, self.app_id)}")
        self.downstream_message_bus.subscribe(t.field_message_bus_app_topic(self.downstream_message_bus.id, self.app_id), self.on_downstream_message)
        self.downstream_message_bus.subscribe(t.field_message_bus_app_topic(self.upstream_message_bus.id, self.app_id), self.on_upstream_message)
        
        _log.debug(f"Subscribing to message on agents topics: \n {t.field_message_bus_agent_topic(self.downstream_message_bus.id, self.agent_id)} \
                                                            \n {t.field_message_bus_agent_topic(self.downstream_message_bus.id, self.agent_id)}")
        self.downstream_message_bus.subscribe(t.field_message_bus_agent_topic(self.downstream_message_bus.id, self.agent_id), self.on_downstream_message)
        self.downstream_message_bus.subscribe(t.field_message_bus_agent_topic(self.upstream_message_bus.id, self.agent_id), self.on_upstream_message)
        
    def subscribe_to_requests(self):
        
        _log.debug(f"Subscribing to requests on agents queue: \n {t.field_agent_request_queue(self.downstream_message_bus.id, self.agent_id)} \
                                                            \n {t.field_agent_request_queue(self.upstream_message_bus.id, self.agent_id)}")
        self.downstream_message_bus.subscribe(t.field_agent_request_queue(self.downstream_message_bus.id, self.agent_id), self.on_request_from_downstream)
        self.downstream_message_bus.subscribe(t.field_agent_request_queue(self.upstream_message_bus.id, self.agent_id), self.on_request_from_uptream)

    def on_measurement(self, headers: Dict, message) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} must be overriden in child class")

    def on_simulation_output(self, headers, message):
        self.on_measurement(headers=headers, message=message)
    
    def on_upstream_message(self, headers: Dict, message) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} must be overriden in child class")
        
    def on_downstream_message(self, headers: Dict, message) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} must be overriden in child class")  
    
    def on_request_from_uptream(self, headers: Dict, message):
        self.on_request(self.upstream_message_bus, headers, message)
    
    def on_request_from_downstream(self, headers: Dict, message):
        self.on_request(self.downstream_message_bus, headers, message)
    
    def on_request(self, message_bus, headers:Dict, message):
        raise NotImplementedError(f"{self.__class__.__name__} must be overriden in child class")
    
    def get_registration_details(self):
        return {'agent_id':str(self.agent_id),
                'app_id':self.app_id,
                'description':self.description,
                'upstream_message_bus_id':self.upstream_message_bus.id,
                'downstream_message_bus_id':self.downstream_message_bus.id
            }
    
            
'''  TODO this has not been implemented yet, so we are commented them out for now.
    # not all agent would use this    
    def on_control(self, control):
        device_id = control.get('device')
        command = control.get('command')
        self.control_device(device_id, command)

    def control_device(self, device_id, command):
        device_topic = self.devices.get(device_id)
        self.secondary_message_bus.publish(device_topic, command)'''


class FeederAgent(DistributedAgent):

    def __init__(self, upstream_message_bus_def: MessageBusDefinition,
                 downstream_message_bus_def: MessageBusDefinition,
                 agent_config: Dict, 
                 feeder_dict=None, simulation_id=None):
        super(FeederAgent, self).__init__(upstream_message_bus_def,
                                          downstream_message_bus_def,
                                          agent_config,
                                          feeder_dict, simulation_id)
        
        if feeder_dict is not None:
            feeder = cim.Feeder(mRID=downstream_message_bus_def.id)
            self.feeder_area = DistributedModel(connection=self.connection, feeder=feeder, topology=feeder_dict)


class SwitchAreaAgent(DistributedAgent):

    def __init__(self, upstream_message_bus_def: MessageBusDefinition, 
                 downstream_message_bus_def: MessageBusDefinition,
                 agent_config: Dict, 
                 switch_area_dict=None, simulation_id=None):
        
        super().__init__(upstream_message_bus_def, 
                                  downstream_message_bus_def,
                                  agent_config,
                                  switch_area_dict, simulation_id)
        
        if switch_area_dict is not None:
            self.switch_area = SwitchArea(downstream_message_bus_def.id, self.connection)
            self.switch_area.initialize_switch_area(switch_area_dict)

    
class SecondaryAreaAgent(DistributedAgent):

    def __init__(self, upstream_message_bus_def: MessageBusDefinition, 
                 downstream_message_bus_def: MessageBusDefinition,
                 agent_config: Dict, 
                 secondary_area_dict=None, simulation_id=None):
        
        super().__init__(upstream_message_bus_def, 
                                                 downstream_message_bus_def,
                                                 agent_config,
                                                 secondary_area_dict, simulation_id)

        if secondary_area_dict is not None:
            self.secondary_area = SecondaryArea(downstream_message_bus_def.id, self.connection)
            self.secondary_area.initialize_secondary_area(secondary_area_dict)


class CoordinatingAgent:
    """
    A CoordinatingAgent performs following functions:
        1. Spawns distributed agents
        2. Publishes compiled output to centralized OT bus
        3. Distributes centralized output to Feeder bus and distributed agents
        4. May have connected devices and control those devices

        upstream, peer , downstream and broadcast
    """

    def __init__(self, feeder_id, system_message_bus_def: MessageBusDefinition, simulation_id=None):
        self.feeder_id = feeder_id
        self.distributed_agents = []

        self.system_message_bus = GridAPPSDMessageBus(system_message_bus_def)
        self.system_message_bus.connect()
        
        #This will change when we have multiple feeders per system
        self.downstream_message_bus = self.system_message_bus
        
        # self.context = ContextManager.getContextByFeeder(self.feeder_id)
        # print(self.context)
        # self.addressable_equipments = self.context['data']['addressable_equipment']
        # self.unaddressable_equipments = self.context['data']['unaddressable_equipment']
        # self.switch_areas = self.context['data']['switch_areas']

        # self.subscribe_to_feeder_bus()

    def spawn_distributed_agent(self, distributed_agent: DistributedAgent):
        distributed_agent.connect()
        self.distributed_agents.append(distributed_agent)


'''    
    def on_control(self, control):
        device_id = control.get('device')
        command = control.get('command')
        self.control_device(device_id, command)

    def publish_to_distribution_bus(self,message):
        self.publish_to_downstream_bus(message)

    def publish_to_distribution_bus_agent(self,agent_id, message):
        self.publish_to_downstream_bus_agent(agent_id, message)

    def control_device(self, device_id, command):
        device_topic = self.devices.get(device_id)
        self.secondary_message_bus.publish(device_topic, command)'''
