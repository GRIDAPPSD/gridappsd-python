import argparse
import json
import logging
import time

from cimgraph.data_profile import CIM_PROFILE

import gridappsd_field_bus.field_interface.agents.agents as agents_mod
from gridappsd_field_bus.field_interface.interfaces import MessageBusDefinition
from gridappsd_field_bus.field_interface.context_managers.context_manager_agents import SubstationAreaContextManager


cim_profile = "cimhub_2023"
agents_mod.set_cim_profile(cim_profile=cim_profile, iec61970_301=8)
cim = agents_mod.cim

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('goss').setLevel(logging.ERROR)
logging.getLogger('stomp.py').setLevel(logging.ERROR)

_log = logging.getLogger(__name__)

def _main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--simulation_id",
        help="Simulation id to use for communicating with simulated devices on the message bus. \
                        If simulation_id is not provided then Context Manager assumes to run on deployed field with real devices.",
        required=False)
    parser.add_argument(
        "-u",
        "--upstream_system_message_bus",
        help="Yaml file to connect with upstream system(OT) message bus.",
        required=True)

    parser.add_argument(
        "-d",
        "--downstream_substation_message_bus",
        help="Yaml file to connect with downstream substation area message bus.",
        type=str,
        required=True)

    parser.add_argument(
        "--substation_dict",
        help="JSON file containing substation topology dictionary. If this file is not provided then disctionary is requested by Field Bus Manager using upstream message bus.",
        type=str,
        required=False)

    opts = parser.parse_args()
    simulation_id = opts.simulation_id

    agent_config = {
        "app_id":
        "context_manager",
        "description":
        "This agent provides topological context information like neighboring agents and devices to other distributed agents"
    }


    system_message_bus_def = MessageBusDefinition.load(opts.upstream_system_message_bus)
    substation_message_bus_def = MessageBusDefinition.load(opts.downstream_substation_message_bus)

    with open(opts.substation_dict,encoding="utf-8") as f:
        substation_dict = json.load(f)["DistributionArea"]["Substations"][0]


    substation_agent = SubstationAreaContextManager(system_message_bus_def,
                                            substation_message_bus_def,
                                            agent_config,
                                            substation_dict = substation_dict,
                                            simulation_id=simulation_id)

    print(substation_agent.context)

    while True:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            print("Exiting sample")
            break


if __name__ == "__main__":
    _main()
