import json
import logging
from pprint import pprint
import sys
import os
from time import sleep

from stomp.exception import ConnectFailedException

from gridappsd import GridAPPSD, topics as t
from gridappsd.simulation import Simulation
# from measureables import get_sensor_config

logging.basicConfig(level=logging.DEBUG)
_log = logging.getLogger(__name__)

logging.getLogger("gridappsd.simulation").setLevel(logging.INFO)

config_file = "history_config.json"

with open(config_file) as fp:
    run_config = json.load(fp)

line_mrid = run_config['power_system_config']['Line_name']

# indx = 0
# node = None
# for node in run_config['service_configs']:
#     if node['id'] == "gridappsd-sensor-simulator":
#         break
# if node is None:
#     raise AttributeError("Sensor service configuration is invalid.")
# node['user_options']['sensors-config'] = get_sensor_config(line_mrid)
import time, datetime

start_time = time.mktime(datetime.datetime.today().timetuple())

try:
    gapps = GridAPPSD()
except ConnectFailedException:
    print("Failed to connect, possible system is not running or login invalid!")
    sys.exit()

if not gapps.connected:
    print("Not connected yet, is the server running?")
    sys.exit()
sim = Simulation(gapps, run_config)

sim_complete = False

fd = open("measurements.txt", 'w')

sim_output = []
measurement_output = []

def onstart(sim):
    print("Sim started: {}".format(sim.simulation_id))


publish_number = 0


def onmeasurment(sim, timestamp, measurements):
    global publish_number

    if not os.path.exists('measurement_first.json'):
        with open("measurement_first.json", "w") as p:
            p.write(json.dumps(measurements, indent=4))
    publish_number += 1
    measurement_output.append(measurements)
    print(f"Publish number: {publish_number} timestamp: {timestamp}")
#    fd.write(f"{json.dumps(measurements)}\n")


def ontimestep(sim, timestep):
    print("next timestep {}".format(timestep))
    #print("Pausing simulation")
    # sim.pause()
    # sleep(2)
    # print("Resuming simulation")
    # sim.resume()


def onfinishsimulation(sim):
    global sim_complete
    sim_complete = True
    fd.close()
    print("Completed simulator")


def on_simulated_output(header, message):
    sim_output.append(message)

sim.add_onstart_callback(onstart)
sim.add_onmesurement_callback(onmeasurment)
sim.add_ontimestep_callback(ontimestep)
sim.add_oncomplete_callback(onfinishsimulation)
sim.start_simulation()
read_topic = t.service_output_topic("gridappsd-sensor-simulator", sim.simulation_id)
gapps.subscribe(read_topic, on_simulated_output)

try:

    while True:
        if sim_complete:
            print("sim output")
            pprint(sim_output)
            break
        sleep(0.1)
except KeyboardInterrupt:
    pass

complete_time = time.mktime(datetime.datetime.today().timetuple())

print(f"Took: {(complete_time - start_time) / 3600} minutes")

for r in sim_output:
    print(r['message']['timestamp'])

