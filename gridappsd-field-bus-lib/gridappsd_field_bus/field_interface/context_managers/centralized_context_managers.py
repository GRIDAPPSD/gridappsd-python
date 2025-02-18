import argparse
import logging
import time

from cimgraph.data_profile import CIM_PROFILE
from gridappsd import GridAPPSD
import gridappsd.topics as t
import gridappsd_field_bus.field_interface.agents.agents as agents_mod
from gridappsd_field_bus.field_interface.context_managers.utils import REQUEST_FIELD, get_message_bus_definition
from gridappsd_field_bus.field_interface.context_managers.context_manager_agents import FeederAreaContextManager, SwitchAreaContextManager, SecondaryAreaContextManager

cim_profile = CIM_PROFILE.CIMHUB_2023.value
agents_mod.set_cim_profile(cim_profile=cim_profile, iec61970_301=7)
cim = agents_mod.cim

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('goss').setLevel(logging.ERROR)
logging.getLogger('stomp.py').setLevel(logging.ERROR)

_log = logging.getLogger(__name__)

def _main():

    time.sleep(10)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--simulation_id",
        help="Simulation id to use for communicating with simulated devices on the message bus. \
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
    response = gapps.get_response(t.PLATFORM_STATUS, {"isField": True})
    field_model_mrid = response['fieldModelMrid']

    is_field_initialized = False

    while not is_field_initialized:
        response = gapps.get_response(REQUEST_FIELD, {"request_type": "is_initilized"})
        print(response)
        is_field_initialized = response['data']['initialized']
        time.sleep(1)


    

    system_message_bus_def = get_message_bus_definition(field_model_mrid)
    feeder_message_bus_def = get_message_bus_definition(field_model_mrid)

    #TODO: create access control for agents for different layers
    feeder_agent = FeederAreaContextManager(system_message_bus_def,
                                            feeder_message_bus_def,
                                            agent_config,
                                            simulation_id=simulation_id)

    #print(feeder_agent.agent_area_dict)
    for switch_area in feeder_agent.agent_area_dict['SwitchAreas']:
        switch_area_message_bus_def = get_message_bus_definition(str(switch_area['@id']))
        print("Creating switch area agent " + str(switch_area['@id']))
        switch_area_agent = SwitchAreaContextManager(feeder_message_bus_def,
                                                     switch_area_message_bus_def,
                                                     agent_config,
                                                     simulation_id=simulation_id,
                                                     switch_area_dict=switch_area)

        # create secondary area distributed agents
        for secondary_area in switch_area['SecondaryAreas']:
            secondary_area_message_bus_def = get_message_bus_definition(
                str(secondary_area['@id']))
            print("Creating secondary area agent " + str(secondary_area['@id']))
            secondary_area_agent = SecondaryAreaContextManager(switch_area_message_bus_def,
                                                               secondary_area_message_bus_def,
                                                               agent_config,
                                                               simulation_id=simulation_id,
                                                               secondary_area_dict=secondary_area)

    while True:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            print("Exiting sample")
            break


if __name__ == "__main__":
    _main()
