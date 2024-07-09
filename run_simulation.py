import json
import logging
import sys
import os
from time import sleep

from stomp.exception import ConnectFailedException

from gridappsd import GridAPPSD, topics as t
from gridappsd.simulation import Simulation

logging.basicConfig(level=logging.DEBUG)
_log = logging.getLogger(__name__)

logging.getLogger("gridappsd.simulation").setLevel(logging.INFO)

sensor_test = {
    "_9c4360bc-13ee-47f0-8a8c-0acb6c2a9930": {
        "class": "Breaker",
        "type": "A"
    },  # Breaker (Analog) (A)
    "_9e76659c-c1e2-47d8-bd97-3a5d31c72bc1": {
        "class": "LoadBreakSwitch",
        "type": "A"
    },  # LoadBreakSwitch (Analog) (A)
    "_8e46d152-edbe-4190-8dfc-d4322bbc6fb8": {
        "class": "ACLineSegment",
        "type": "PNV"
    },  # ACLineSegment (Analog) (PNV)
    "_91c8096b-527e-4b17-9b60-608c2e89b0ef": {
        "class": "PowerTransformer",
        "type": "PNV"
    },  # PowerTransformer (Analog) (PNV)
    "_7a5ce176-8185-4118-8f49-d1628692d783": {
        "class": "ACLineSegment",
        "type": "VA"
    },  # ACLineSegment (Analog) (VA)
    "_d3fc08bf-ab76-4bba-a3c3-b8de144310f7": {
        "class": "PowerTransformer",
        "type": "VA"
    },  # PowerTransformer (Analog) (VA)
    "_81ebcbfc-f8fe-4b7d-9735-0b00356b24dd": {
        "class": "Breaker",
        "type": "Pos"
    },  # Breaker (Discrete) (Pos)
    "_9530188b-b0f6-4337-84ec-2fc9282740b3": {
        "class": "Recloser",
        "type": "Pos"
    },  # Recloser (Discrete) (Pos)
}
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
    os.environ['GRIDAPPSD_USER'] = 'system'
    os.environ['GRIDAPPSD_PASSWORD'] = 'manager'
    os.environ['GRIDAPPSD_ADDRESS'] = 'gridappsd'
    gapps = GridAPPSD(goss_log_level=logging.INFO)
except ConnectFailedException:
    print(
        "Failed to connect, possible system is not running or login invalid!")
    sys.exit()

if not gapps.connected:
    print("Not connected yet, is the server running?")
    sys.exit()
sim = Simulation(gapps, run_config)

sim_complete = False

# fd = open("measurements.txt", 'w')

sim_output = []
measurement_output = []


def onstart(sim):
    _log.info("Sim started: {}".format(sim.simulation_id))


publish_number = 0
sim_publish_number = 0


def onmeasurment(sim, timestamp, measurements):
    global publish_number
    publish_number += 1
    #
    # for k, v in measurements.items():
    #
    #     v['timestamp'] = timestamp
    #     #
    #     # v['class'] = sensor_test[k]['class']
    #     # v['type'] = sensor_test[k]['type']
    #     measurement_output.append(v)
    _log.info("{timestamp} publish number: {publish_number}".format(
        publish_number=publish_number, timestamp=timestamp))


#    fd.write(f"{json.dumps(measurements)}\n")


def ontimestep(sim, timestep):
    _log.info("next timestep {timestep}".format(timestep=timestep))
    #print("Pausing simulation")
    # sim.pause()
    # sleep(2)
    # print("Resuming simulation")
    # sim.resume()


def onfinishsimulation(sim):
    global sim_complete
    sim_complete = True
    # fd.close()
    _log.info("Simulation complete")


def on_simulated_output(header, message):
    global sim_publish_number
    sim_publish_number += 1
    timestamp = message['message']['timestamp']
    _log.info(
        "{timestamp} simulation publish number: {sim_publish_number} timestamp: {timestamp}"
        .format(timestamp=timestamp, sim_publish_number=sim_publish_number))
    # print('SIMULATED MESSAGE IS HERE!')
    # measurements = message['message']['measurements']
    # timestamp = message['message']['timestamp']
    # for k, v in measurements.items():
    #
    #     v['timestamp'] = timestamp
    #     # v['class'] = sensor_test[k]['class']
    #     # v['type'] = sensor_test[k]['type']
    #     sim_output.append(v)


sim.add_onstart_callback(onstart)
sim.add_onmeasurement_callback(onmeasurment)
sim.add_ontimestep_callback(ontimestep)
sim.add_oncomplete_callback(onfinishsimulation)
sim.start_simulation()
read_topic = t.service_output_topic("gridappsd-sensor-simulator",
                                    sim.simulation_id)
_log.debug("Reading topic for sensor output {read_topic}".format(
    read_topic=read_topic))
gapps.subscribe(read_topic, on_simulated_output)

try:

    while True:
        if sim_complete:
            # print("sim output")
            # pprint(sim_output)
            break
        sleep(0.1)
except KeyboardInterrupt:
    pass

# Sleep to write to influx hopefully not necessary
sleep(180)
complete_time = time.mktime(datetime.datetime.today().timetuple())

print(f"Took: {(complete_time - start_time) / 3600} minutes")

# with open("sim_output.txt", 'w') as fp:
#     fp.write(json.dumps(sim_output, indent=4))
#
# with open("measuremnt_output.txt", 'w') as fp:
#     fp.write(json.dumps(measurement_output, indent=4))
