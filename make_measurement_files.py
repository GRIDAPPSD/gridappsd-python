import json
import threading

import yaml
from gridappsd import GridAPPSD
from gridappsd.simulation import Simulation
from gridappsd.topics import simulation_output_topic
from queue import Queue
import os

os.environ["GRIDAPPSD_USER"] = "system"
os.environ["GRIDAPPSD_PASSWORD"] = "manager"
os.environ["GRIDAPPSD_ADDRESS"] = "gridappsd"
os.environ["GRIDAPPSD_PORT"] = "61613"
output_queue = Queue()
gapps = GridAPPSD()

with open("/repos/gridappsd-python/examples/default_run_simulation_ieee9500_final_config.yaml") as fp:
    config = yaml.safe_load(fp)
sim = Simulation(gapps=gapps,
                 run_config=config)

sim_id = sim.start_simulation()

def data_output(topic, message):
    print(f"data_output {json.dumps(message)[:50]}")
    output_queue.put(message)

gapps.subscribe(simulation_output_topic(sim.simulation_id), data_output)

def write_thread(queue, filename):
    with open(filename, "w") as f:
        while True:
            content = queue.get()
            if content == "DONE":
                return
            f.write(json.dumps(content))

wthread = threading.Thread(target=write_thread,
                           args=(output_queue, "messages.json"))
wthread.daemon = True
wthread.start()

sim.run_loop()

output_queue.put("DONE")

