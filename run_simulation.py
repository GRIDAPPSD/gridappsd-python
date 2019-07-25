import logging
from pprint import pprint
import sys
from time import sleep

from stomp.exception import ConnectFailedException

from gridappsd import GridAPPSD
from gridappsd.simulation import Simulation

logging.basicConfig(level=logging.DEBUG)
_log = logging.getLogger(__name__)
# 123-based model
# "power_system_config": {
#                            "GeographicalRegion_name": "_73C512BD-7249-4F50-50DA-D93849B89C43",
#                            "SubGeographicalRegion_name": "_1CD7D2EE-3C91-3248-5662-A43EFEFAC224",
#                            "Line_name": "_C1C3E687-6FFD-C753-582B-632A27E28507"
#                        },

# 8500-based model
# {"power_system_config": {
#     "GeographicalRegion_name":"_73C512BD-7249-4F50-50DA-D93849B89C43",
#     "SubGeographicalRegion_name":"_A1170111-942A-6ABD-D325-C64886DC4D7D",
#     "Line_name":"_4F76A5F9-271D-9EB8-5E31-AA362D86F2C3"},


run_config = {
    "power_system_config": {
        # 9500 node system
        #"Line_name": "_AAE94E4A-2465-6F5E-37B1-3E72183A4E44",

        # 8500 node system
        # "Line_name": "_4F76A5F9-271D-9EB8-5E31-AA362D86F2C3",
        # 123 node
        "Line_name": "_4F76A5F9-271D-9EB8-5E31-AA362D86F2C3"

        # "GeographicalRegion_name": "_73C512BD-7249-4F50-50DA-D93849B89C43",
        # "SubGeographicalRegion_name": "_1CD7D2EE-3C91-3248-5662-A43EFEFAC224",
        # "Line_name": "_C1C3E687-6FFD-C753-582B-632A27E28507"
    },
    "application_config": {
        "applications": [{"name": "sample_app", "config_string": ""}]
    },
    "simulation_config": {
        "start_time": "1562453292",
        "duration": "10",
        "simulator": "GridLAB-D",
        "timestep_frequency": "1000",
        "timestep_increment": "1000",
        "run_realtime": False,
        "simulation_name": "simulation_name",
        "power_flow_solver_method": "NR",
        "model_creation_config": {
            "load_scaling_factor": "1",
            "schedule_name": "ieeezipload",
            "z_fraction": "0",
            "i_fraction": "1",
            "p_fraction": "0",
            "randomize_zipload_fractions": False,
            "use_houses": True
        }
    },
    "test_config": {
        "events": [],
        "appId": "sample_app" #"#"_C1C3E687-6FFD-C753-582B-632A27E28507"
    }
}


try:
    gapps = GridAPPSD()
except ConnectFailedException:
    print("Login possibly invalid!")
    sys.exit()

if not gapps.connected:
    print("Not connected yet, is the server running?")
    sys.exit()
sim = Simulation(gapps, run_config)

sim_complete = False


def onstart(sim):
    print("Sim started")


def onmeasurment(sim, timestamp, measurements):
    pass


def ontimestep(sim, timestep):
    print("next timestep {}".format(timestep))
    print("Pausing simulation")
    sim.pause()
    sleep(2)
    print("Resuming simulation")
    sim.resume()


def onfinishsimulation(sim):
    global sim_complete
    sim_complete = True
    print("Completed simulator")

sim.add_onstart_callback(onstart)
sim.add_onmesurement_callback(onmeasurment)
sim.add_ontimestep_callback(ontimestep)
sim.add_oncomplete_callback(onfinishsimulation)
sim.start_simulation()

try:

    while True:
        if sim_complete:
            break
        sleep(0.1)
except KeyboardInterrupt:
    pass