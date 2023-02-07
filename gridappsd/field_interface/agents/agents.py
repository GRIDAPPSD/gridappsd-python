from typing import Dict
import cimlab.data_profile.cimext_2022 as cim

from abc import abstractmethod
from dataclasses import dataclass, field
import importlib
import logging

from gridappsd.field_interface.context import ContextManager

from cimlab.loaders import Parameter, ConnectionParameters
from cimlab.loaders.gridappsd import GridappsdConnection, get_topology_response
from cimlab.models import SwitchArea, SecondaryArea, DistributedModel

from gridappsd.field_interface.gridappsd_field_bus import GridAPPSDMessageBus
from gridappsd.field_interface.interfaces import MessageBusDefinition

import cimlab.data_profile.cimext_2022 as cim
from cimlab.loaders import Parameter, ConnectionParameters
from cimlab.loaders import gridappsd
from cimlab.loaders.gridappsd import GridappsdConnection, get_topology_response
from cimlab.models import SwitchArea, SecondaryArea, DistributedModel


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
                 agent_dict=None,
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
        self.params = ConnectionParameters()
        self.connection = GridappsdConnection(self.params)

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

    @classmethod
    def from_feeder(cls, feeder_id, area_id):
        context = ContextManager.get_context_by_feeder(feeder_id, area_id)
        return cls(context.get('upstream_message_bus_def'), context.get('downstream_message_bus_def'))

    def connect(self):
        if self.upstream_message_bus is not None:
            self.upstream_message_bus.connect()
        if self.downstream_message_bus is not None:
            self.downstream_message_bus.connect()
        if self.downstream_message_bus is None and self.upstream_message_bus is None:
            raise ValueError("Either upstream or downstream bus must be specified!")
        self.subscribe_to_measurement()

    def subscribe_to_measurement(self):
        if self.simulation_id is None:
            self.downstream_message_bus.subscribe(f"fieldbus/{self.downstream_message_bus.id}", self.on_measurement)
        else:
            topic = f"/topic/goss.gridappsd.field.simulation.output.{self.simulation_id}.{self.downstream_message_bus.id}"
            _log.debug(f"subscribing to sim_output on topic {topic}")
            self.downstream_message_bus.subscribe(topic,
                                                  self.on_simulation_output)

    def on_measurement(self, headers: Dict, message) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} must be overriden in child class")

    def on_simulation_output(self, headers, message):
        self.on_measurement(headers=headers, message=message)


'''  TODO this has not been implemented yet, so we are commented them out for now.
    # not all agent would use this    
    def on_control(self, control):
        device_id = control.get('device')
        command = control.get('command')
        self.control_device(device_id, command)

    def publish_to_upstream_bus(self,output):
        self.switch_message_bus.publish(self.output_topic, output)

    # could be and upstream or peer level agent
    def publish_to_upstream_bus_agent(self,agent_id, output):
        self.switch_message_bus.publish(self.topic.agent_id, output)

    def publish_to_downstream_bus(self,message):
        self.secondary_message_bus.publish(self.topic, message)

    # downstream agent
    def publish_to_downstream_bus_agent(self,agent_id, message):
        self.secondary_message_bus.publish(self.topic.agent_id, message)

    def control_device(self, device_id, command):
        device_topic = self.devices.get(device_id)
        self.secondary_message_bus.publish(device_topic, command)'''


class FeederAgent(DistributedAgent):

    def __init__(self, upstream_message_bus_def: MessageBusDefinition,
                 downstream_message_bus_def: MessageBusDefinition,
                 feeder_dict=None, simulation_id=None):
        super(FeederAgent, self).__init__(upstream_message_bus_def,
                                          downstream_message_bus_def,
                                          feeder_dict, simulation_id)
        
        if feeder_dict is not None:
            feeder = cim.Feeder(mRID=downstream_message_bus_def.id)

            self.feeder_area = DistributedModel(connection=self.connection, feeder=feeder, topology=feeder_dict)


class SwitchAreaAgent(DistributedAgent):

    def __init__(self, upstream_message_bus_def: MessageBusDefinition, 
                 downstream_message_bus_def: MessageBusDefinition,
                 switch_area_dict=None, simulation_id=None):
        
        super().__init__(upstream_message_bus_def, 
                                  downstream_message_bus_def,
                                  switch_area_dict, simulation_id)
        
        if switch_area_dict is not None:
            self.switch_area = SwitchArea(downstream_message_bus_def.id, self.connection)
            self.switch_area.initialize_switch_area(switch_area_dict)

    
class SecondaryAreaAgent(DistributedAgent):

    def __init__(self, upstream_message_bus_def: MessageBusDefinition, 
                 downstream_message_bus_def: MessageBusDefinition,
                 secondary_area_dict=None, simulation_id=None):
        
        super().__init__(upstream_message_bus_def, 
                                                 downstream_message_bus_def,
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
    def on_message_from_feeder_bus(self, message):
        pass

    def subscribe_to_distribution_bus(self, topic):
        #self.system_message_bus.subscribe("/topic/goss.gridappsd.field."+self.feeder_id, 
        self.on_message_from_feeder_bus)
        self.system_message_bus.subscribe(topic, self.on_message_from_feeder_bus)

    def subscribe_to_feeder_bus(self, topic):
        self.system_message_bus.subscribe(topic, self.on_message_from_feeder_bus)

    def on_measurement(self, measurements):
        print(measurements)

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
