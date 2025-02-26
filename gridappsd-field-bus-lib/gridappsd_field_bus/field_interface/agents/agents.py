import dataclasses
import importlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict

from cimgraph.databases import ConnectionParameters
from cimgraph.databases.gridappsd import GridappsdConnection
from cimgraph.models import FeederModel
from cimgraph.models.distributed_area import DistributedArea

from gridappsd import DifferenceBuilder
import gridappsd.topics as t
from gridappsd_field_bus.field_interface.context import LocalContext
from gridappsd_field_bus.field_interface.gridappsd_field_bus import GridAPPSDMessageBus
from gridappsd_field_bus.field_interface.interfaces import (FieldMessageBus, MessageBusDefinition, MessageBusFactory)

CIM_PROFILE = None
IEC61970_301 = None
cim = None

_log = logging.getLogger(__name__)


def set_cim_profile(cim_profile: str, iec61970_301: int):
    global CIM_PROFILE
    global IEC61970_301
    global cim
    CIM_PROFILE = cim_profile
    IEC61970_301 = iec61970_301
    cim = importlib.import_module('cimgraph.data_profile.' + cim_profile)


@dataclass
class AgentRegistrationDetails:
    agent_id: str
    app_id: str
    description: str
    upstream_message_bus_id: FieldMessageBus.id
    downstream_message_bus_id: FieldMessageBus.id


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

        # TODO: Change params and connection to local connection
        self.params = ConnectionParameters(cim_profile=CIM_PROFILE, iec61970_301=IEC61970_301)

        self.connection = GridappsdConnection(self.params)
        self.connection.cim_profile = cim_profile

        self.app_id = agent_config['app_id']
        self.description = agent_config['description']
        dt = datetime.now()
        ts = datetime.timestamp(dt)
        if ('context_manager' not in self.app_id):
            self.agent_id = "da_" + self.app_id
        else:
            self.agent_id = downstream_message_bus_def.id + '.context_manager'

        self.agent_area_dict = agent_area_dict

        if upstream_message_bus_def is not None:
            if upstream_message_bus_def.is_ot_bus:
                self.upstream_message_bus = MessageBusFactory.create(upstream_message_bus_def)
        #            else:
        #                self.upstream_message_bus = VolttronMessageBus(upstream_message_bus_def)

        if downstream_message_bus_def is not None:
            if downstream_message_bus_def.is_ot_bus:
                self.downstream_message_bus = MessageBusFactory.create(downstream_message_bus_def)
        #            else:
        #                self.downstream_message_bus = VolttronMessageBus(downstream_message_bus_def)

        # self.context = ContextManager.get(self.feeder_id, self.area_id)

        # if agent_dict is not None:
        #    self.addressable_equipments = agent_dict['addressable_equipment']
        #    self.unaddressable_equipments = agent_dict['unaddressable_equipment']

    def _connect(self):

        if self.upstream_message_bus is not None:
            self.upstream_message_bus.connect()
        if self.downstream_message_bus is not None:
            self.downstream_message_bus.connect()
        if self.downstream_message_bus is None and self.upstream_message_bus is None:
            raise ValueError("Either upstream or downstream bus must be specified!")

        if ('context_manager' not in self.app_id):
            self.agent_id = "da_" + self.app_id + "_" + self.downstream_message_bus.id

        if self.agent_area_dict is None:
            context = LocalContext.get_context_by_message_bus(self.downstream_message_bus)
            self.agent_area_dict = context['data']

        self.subscribe_to_measurement()
        self.subscribe_to_messages()
        self.subscribe_to_requests()

        if ('context_manager' not in self.app_id):
            LocalContext.register_agent(self.downstream_message_bus, self.upstream_message_bus,
                                        self)

    def disconnect(self):

        if self.upstream_message_bus is not None:
            self.upstream_message_bus.disconnect()
        if self.downstream_message_bus is not None:
            self.downstream_message_bus.disconnect()

    def subscribe_to_measurement(self):
        if self.simulation_id is None:
            self.downstream_message_bus.subscribe(
                t.field_output_topic(self.downstream_message_bus.id), self.on_measurement)
        else:
            topic = t.field_output_topic(self.downstream_message_bus.id, self.simulation_id)
            _log.debug(f"subscribing to simulation output on topic {topic}")
            self.downstream_message_bus.subscribe(topic, self.on_simulation_output)

    def subscribe_to_messages(self):

        self.downstream_message_bus.subscribe(
            t.field_message_bus_topic(self.downstream_message_bus.id), self.on_downstream_message)
        self.upstream_message_bus.subscribe(
            t.field_message_bus_topic(self.upstream_message_bus.id), self.on_upstream_message)

        _log.debug(
            f"Subscribing to messages on application topics: \n {t.field_message_bus_app_topic(self.downstream_message_bus.id, self.app_id)} \
                                                                    \n {t.field_message_bus_app_topic(self.upstream_message_bus.id, self.app_id)}"
        )
        self.downstream_message_bus.subscribe(
            t.field_message_bus_app_topic(self.downstream_message_bus.id, self.app_id),
            self.on_downstream_message)
        self.upstream_message_bus.subscribe(
            t.field_message_bus_app_topic(self.upstream_message_bus.id, self.app_id),
            self.on_upstream_message)

        if ('context_manager' not in self.app_id):
            _log.debug(
                f"Subscribing to message on agents topics: \n {t.field_message_bus_agent_topic(self.downstream_message_bus.id, self.agent_id)} \
                                                                \n {t.field_message_bus_agent_topic(self.upstream_message_bus.id, self.agent_id)}"
            )
            self.downstream_message_bus.subscribe(
                t.field_message_bus_agent_topic(self.downstream_message_bus.id, self.agent_id),
                self.on_downstream_message)
            self.upstream_message_bus.subscribe(
                t.field_message_bus_agent_topic(self.upstream_message_bus.id, self.agent_id),
                self.on_upstream_message)

    def subscribe_to_requests(self):

        _log.debug(
            f"Subscribing to requests on agents queue: \n {t.field_agent_request_queue(self.downstream_message_bus.id, self.agent_id)} \
                                                            \n {t.field_agent_request_queue(self.upstream_message_bus.id, self.agent_id)}"
        )
        self.downstream_message_bus.subscribe(
            t.field_agent_request_queue(self.downstream_message_bus.id, self.agent_id),
            self.on_request_from_downstream)
        self.upstream_message_bus.subscribe(
            t.field_agent_request_queue(self.upstream_message_bus.id, self.agent_id),
            self.on_request_from_uptream)

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

    def on_request(self, message_bus, headers: Dict, message):
        raise NotImplementedError(f"{self.__class__.__name__} must be overriden in child class")

    def get_registration_details(self):
        details = AgentRegistrationDetails(str(self.agent_id), self.app_id, self.description,
                                           self.upstream_message_bus.id,
                                           self.downstream_message_bus.id)
        return dataclasses.asdict(details)

    def publish_downstream(self, message):
        self.downstream_message_bus.send(t.field_message_bus_topic(self.downstream_message_bus.id),
                                         message)

    def publish_upstream(self, message):
        self.upstream_message_bus.send(t.field_message_bus_topic(self.upstream_message_bus.id),
                                       message)

    def send_control_command(self, differenceBuilder: DifferenceBuilder):
        if self.simulation_id is not None:
            LocalContext.send_control_command(self.downstream_message_bus, differenceBuilder)

    '''
        TODO This block needs to be tested with device interface
        else:
        self.downstream_message_bus.send(devie_interface_topic, differenceBuilder)
    '''


'''  TODO this has not been implemented yet, so we are commented them out for now.
    # not all agent would use this
    def on_control(self, control):
        device_id = control.get('device')
        command = control.get('command')
        self.control_device(device_id, command)
'''

class SubstationAgent(DistributedAgent):

    def __init__(self,
                 upstream_message_bus_def: MessageBusDefinition,
                 downstream_message_bus_def: MessageBusDefinition,
                 agent_config: Dict,
                 substation_dict=None,
                 simulation_id=None):
        super().__init__(upstream_message_bus_def, downstream_message_bus_def, agent_config,
                         substation_dict, simulation_id)
        self.substation_area = None
        self.downstream_message_bus_def = downstream_message_bus_def

        self._connect()

        if self.agent_area_dict is not None:
            substation = cim.Substation(mRID=self.downstream_message_bus_def.id)
            self.substation_area = DistributedArea(connection=self.connection,
                                               container=substation,
                                               distributed=True)
            self.substation_area.build_from_topo_message(topology_dict=self.agent_area_dict)

class FeederAgent(DistributedAgent):

    def __init__(self,
                 upstream_message_bus_def: MessageBusDefinition,
                 downstream_message_bus_def: MessageBusDefinition,
                 agent_config: Dict,
                 feeder_dict=None,
                 simulation_id=None):
        super().__init__(upstream_message_bus_def, downstream_message_bus_def, agent_config,
                         feeder_dict, simulation_id)
        self.feeder_area = None
        self.downstream_message_bus_def = downstream_message_bus_def

        self._connect()

        if self.agent_area_dict is not None:
            feeder = cim.FeederArea(mRID=self.downstream_message_bus_def.id)
            self.feeder_area = DistributedArea(connection=self.connection,
                                               container=feeder,
                                               distributed=True)
            self.feeder_area.build_from_topo_message(topology_dict=self.agent_area_dict)


class SwitchAreaAgent(DistributedAgent):

    def __init__(self,
                 upstream_message_bus_def: MessageBusDefinition,
                 downstream_message_bus_def: MessageBusDefinition,
                 agent_config: Dict,
                 switch_area_dict=None,
                 simulation_id=None):
        super().__init__(upstream_message_bus_def, downstream_message_bus_def, agent_config,
                         switch_area_dict, simulation_id)
        self.switch_area = None
        self.downstream_message_bus_def = downstream_message_bus_def

        self._connect()

        if self.agent_area_dict is not None:
            container = cim.SwitchArea(mRID=self.downstream_message_bus_def.id)
            self.switch_area = DistributedArea(container=container,
                                               connection=self.connection,
                                               distributed=True)
            self.switch_area.build_from_topo_message(topology_dict=self.agent_area_dict)


class SecondaryAreaAgent(DistributedAgent):

    def __init__(self,
                 upstream_message_bus_def: MessageBusDefinition,
                 downstream_message_bus_def: MessageBusDefinition,
                 agent_config: Dict,
                 secondary_area_dict=None,
                 simulation_id=None):
        super().__init__(upstream_message_bus_def, downstream_message_bus_def, agent_config,
                         secondary_area_dict, simulation_id)
        self.secondary_area = None
        self.downstream_message_bus_def = downstream_message_bus_def

        self._connect()

        if self.agent_area_dict is not None:
            if len(self.agent_area_dict['AddressableEquipment']) == 0:
                _log.warning(
                    f"No addressable equipment in the secondary area with down stream message bus id: {self.downstream_message_bus.id}."
                )
            container = cim.SecondaryArea(mRID=self.downstream_message_bus_def.id)
            self.secondary_area = DistributedArea(container=container,
                                                  connection=self.connection,
                                                  distributed=True)
            self.secondary_area.build_from_topo_message(topology_dict=self.agent_area_dict)


class CoordinatingAgent:
    """
    A CoordinatingAgent performs following functions:
        1. Spawns distributed agents
        2. Publishes compiled output to centralized OT bus
        3. Distributes centralized output to Feeder bus and distributed agents
        4. May have connected devices and control those devices

        upstream, peer , downstream and broadcast
    """

    def __init__(self,
                 feeder_id,
                 system_message_bus_def: MessageBusDefinition,
                 simulation_id=None):
        self.feeder_id = feeder_id
        self.distributed_agents = []

        self.system_message_bus = MessageBusFactory.create(system_message_bus_def)
        self.system_message_bus.connect()

        # This will change when we have multiple feeders per system
        self.downstream_message_bus = self.system_message_bus

        # self.context = ContextManager.getContextByFeeder(self.feeder_id)
        # print(self.context)
        # self.addressable_equipments = self.context['data']['addressable_equipment']
        # self.unaddressable_equipments = self.context['data']['unaddressable_equipment']
        # self.switch_areas = self.context['data']['switch_areas']

        # self.subscribe_to_feeder_bus()


''' def spawn_distributed_agent(self, distributed_agent: DistributedAgent):
        distributed_agent.connect()
        self.distributed_agents.append(distributed_agent)

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
