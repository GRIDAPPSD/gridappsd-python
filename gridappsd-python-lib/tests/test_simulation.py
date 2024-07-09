# import json
# # from pprint import pprint
# import logging
# import os
# import sys
# import time
# import pytest

# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# from gridappsd import GridAPPSD, topics as t
# from gridappsd.simulation import Simulation

# # The directory containing this file
# HERE = os.path.dirname(__file__)

# def base_config():
#     data = {"power_system_config":{"SubGeographicalRegion_name":"_ABEB635F-729D-24BF-B8A4-E2EF268D8B9E","GeographicalRegion_name":"_73C512BD-7249-4F50-50DA-D93849B89C43","Line_name":"_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62"},"simulation_config":{"power_flow_solver_method":"NR","duration":120,"simulation_name":"ieee13nodeckt","simulator":"GridLAB-D","start_time":1605418946,"run_realtime":False,"simulation_output":{},"model_creation_config":{"load_scaling_factor":1.0,"triplex":"y","encoding":"u","system_frequency":60,"voltage_multiplier":1.0,"power_unit_conversion":1.0,"unique_names":"y","schedule_name":"ieeezipload","z_fraction":0.0,"i_fraction":1.0,"p_fraction":0.0,"randomize_zipload_fractions":False,"use_houses":False},"simulation_broker_port":51044,"simulation_broker_location":"127.0.0.1"},"application_config":{"applications":[]},"service_configs":[],"test_config":{"randomNum":{"seed":{"value":185213303967438},"nextNextGaussian":0.0,"haveNextNextGaussian":False},"events":[],"testInput":True,"testOutput":True,"appId":"","testId":"1468836560","testType":"simulation_vs_expected","storeMatches":False},"simulation_request_type":"NEW"}
#     # with open("{HERE}/simulation_fixtures/13_node_2_min_base.json".format(HERE=HERE)) as fp:
#     #     data = json.load(fp)
#     return data

# def test_simulation_no_duplicate_measurement_timestamps(gridappsd_client: GridAPPSD):
#     num_measurements = 0
#     timestamps = set()

#     def measurement(sim, timestamp, measurement):
#         nonlocal num_measurements
#         num_measurements += 1
#         assert timestamp not in timestamps
#         timestamps.add(timestamp)

#     gapps = gridappsd_client
#     sim = Simulation(gapps, base_config())
#     sim.add_onmeasurement_callback(measurement)
#     sim.start_simulation()
#     sim.run_loop()

#     # did we get a measurement?
#     assert num_measurements > 0

#     # if empty then we know the simulation did not work.
#     assert timestamps
