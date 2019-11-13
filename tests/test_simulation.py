import json
# from pprint import pprint
import os
import time
import pytest

from gridappsd import GridAPPSD, topics as t
from gridappsd.simulation import Simulation

# The directory containing this file
HERE = os.path.dirname(__file__)

@pytest.fixture
def gappsd():

    gappsd = GridAPPSD()
    yield gappsd
    gappsd.disconnect()
    gappsd = None


@pytest.fixture
def base_config():
    with open("{HERE}/simulation_fixtures/13_node_2_min_base.json".format(HERE=HERE)) as fp:
        data = json.load(fp)
    yield data


def test_simulation_no_duplicate_measurement_timestamps(gappsd, base_config):
    sim = Simulation(gappsd, base_config)
    timestampset = set()
    timestampset2 = set()
    complete = False

    def onmeasurement(sim, timestamp, measurements):
        nonlocal timestampset
        #assert timestamp not in timestampset
        print(f"timestamp is {timestamp}")
        timestampset.add(timestamp)

    def onsubscribetooutput(header, message):
        nonlocal timestampset2
        timestamp = message['message']['timestamp']
        assert timestamp not in timestampset2
        timestampset2.add(timestamp)

    def oncomplete(sim):
        nonlocal complete
        complete = True

    sim.add_onmesurement_callback(onmeasurement)
    sim.add_oncomplete_callback(oncomplete)
    sim.start_simulation()
    gappsd.subscribe(t.simulation_output_topic(sim.simulation_id), onsubscribetooutput)
    going = 0
    while not complete:
        going += 1
        if going % 1000 == 0:
            print(f"Going: {going}")
        time.sleep(0.1)


# from gridappsd import GridAPPSD
#
# # model_map = {
# #
# # {"configurationType":"CIM Dictionary","parameters":{"model_id":"_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62"}}
# # }
# from gridappsd.simulation import Simulation
#
# models = dict(ieee123=u'_C1C3E687-6FFD-C753-582B-632A27E28507',
#               ieee8500=u'_4F76A5F9-271D-9EB8-5E31-AA362D86F2C3',
#               ieee13nodeckt=u'_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62')
#
# run_config_123 = {
#     "power_system_config": {
#         "GeographicalRegion_name": "_73C512BD-7249-4F50-50DA-D93849B89C43",
#         "SubGeographicalRegion_name": "_1CD7D2EE-3C91-3248-5662-A43EFEFAC224",
#         "Line_name": "_C1C3E687-6FFD-C753-582B-632A27E28507"
#     },
#     "application_config": {
#         "applications": []
#     },
#     "simulation_config": {
#         "start_time": "1562453292",
#         "duration": "20",
#         "simulator": "GridLAB-D",
#         "timestep_frequency": "1000",
#         "timestep_increment": "1000",
#         "run_realtime": True,
#         "simulation_name": "ieee123",
#         "power_flow_solver_method": "NR",
#         "model_creation_config": {
#             "load_scaling_factor": "1",
#             "schedule_name": "ieeezipload",
#             "z_fraction": "0",
#             "i_fraction": "1",
#             "p_fraction": "0",
#             "randomize_zipload_fractions": False,
#             "use_houses": False
#         }
#     },
#     "test_config": {
#         "events": [],
#         "appId": "_C1C3E687-6FFD-C753-582B-632A27E28507"
#     }
# }
#
#
# revmodels = dict()
# for k, v in models.items():
#     revmodels[v] = k
#
# # {u'models': [{u'modelId': u'_77966920-E1EC-EE8A-23EE-4EFD23B205BD',
# #                         u'modelName': u'acep_psil',
# #                         u'regionId': u'_96465E7A-6EC3-ECCA-BC27-31B53F05C96E',
# #                         u'regionName': u'Alaska',
# #                         u'stationId': u'_22B12048-23DF-007B-9291-826A16DBCB21',
# #                         u'stationName': u'UAF',
# #                         u'subRegionId': u'_2F8FC9BF-FF32-A197-D541-0A2529D04DF7',
# #                         u'subRegionName': u'Fairbanks'},
# #                        {u'modelId': u'_C1C3E687-6FFD-C753-582B-632A27E28507',
# #                         u'modelName': u'ieee123',
# #                         u'regionId': u'_73C512BD-7249-4F50-50DA-D93849B89C43',
# #                         u'regionName': u'IEEE',
# #                         u'stationId': u'_FE44B314-385E-C2BF-3983-3A10C6060022',
# #                         u'stationName': u'IEEE123',
# #                         u'subRegionId': u'_1CD7D2EE-3C91-3248-5662-A43EFEFAC224',
# #                         u'subRegionName': u'Medium'},
# #                        {u'modelId': u'_E407CBB6-8C8D-9BC9-589C-AB83FBF0826D',
# #                         u'modelName': u'ieee123pv',
# #                         u'regionId': u'_73C512BD-7249-4F50-50DA-D93849B89C43',
# #                         u'regionName': u'IEEE',
# #                         u'stationId': u'_FE44B314-385E-C2BF-3983-3A10C6060022',
# #                         u'stationName': u'IEEE123',
# #                         u'subRegionId': u'_1CD7D2EE-3C91-3248-5662-A43EFEFAC224',
# #                         u'subRegionName': u'Medium'},
# #                        {u'modelId': u'_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62',
# #                         u'modelName': u'ieee13nodeckt',
# #                         u'regionId': u'_73C512BD-7249-4F50-50DA-D93849B89C43',
# #                         u'regionName': u'IEEE',
# #                         u'stationId': u'_6C62C905-6FC7-653D-9F1E-1340F974A587',
# #                         u'stationName': u'IEEE13',
# #                         u'subRegionId': u'_ABEB635F-729D-24BF-B8A4-E2EF268D8B9E',
# #                         u'subRegionName': u'Small'},
# #                        {u'modelId': u'_5B816B93-7A5F-B64C-8460-47C17D6E4B0F',
# #                         u'modelName': u'ieee13nodecktassets',
# #                         u'regionId': u'_73C512BD-7249-4F50-50DA-D93849B89C43',
# #                         u'regionName': u'IEEE',
# #                         u'stationId': u'_6C62C905-6FC7-653D-9F1E-1340F974A587',
# #                         u'stationName': u'IEEE13',
# #                         u'subRegionId': u'_ABEB635F-729D-24BF-B8A4-E2EF268D8B9E',
# #                         u'subRegionName': u'Small'},
# #                        {u'modelId': u'_4F76A5F9-271D-9EB8-5E31-AA362D86F2C3',
# #                      a   u'modelName': u'ieee8500',
# #                         u'regionId': u'_73C512BD-7249-4F50-50DA-D93849B89C43',
# #                         u'regionName': u'IEEE',
# #                         u'stationId': u'_F1E8E479-5FA0-4BFF-8173-B375D25B0AA2',
# #                         u'stationName': u'IEEE8500',
# #                         u'subRegionId': u'_A1170111-942A-6ABD-D325-C64886DC4D7D',
# #                         u'subRegionName': u'Large'},
# #                        {u'modelId': u'_AAE94E4A-2465-6F5E-37B1-3E72183A4E44',
# #                         u'modelName': u'ieee8500new_335',
# #                         u'regionId': u'_73C512BD-7249-4F50-50DA-D93849B89C43',
# #                         u'regionName': u'IEEE',
# #                         u'stationId': u'_40485321-9B2C-1B8C-EC33-39D2F7948163',
# #                         u'stationName': u'ThreeSubs',
# #                         u'subRegionId': u'_A1170111-942A-6ABD-D325-C64886DC4D7D',
# #                         u'subRegionName': u'Large'},
# #                        {u'modelId': u'_67AB291F-DCCD-31B7-B499-338206B9828F',
# #                         u'modelName': u'j1',
# #                         u'regionId': u'_9A1E61E4-5CF1-982B-C7EF-0918D26645C7',
# #                         u'regionName': u'EPRI',
# #                         u'stationId': u'_A3C31EE7-4EE6-A167-87C7-915B1C6E97F0',
# #                         u'stationName': u'J1',
# #                         u'subRegionId': u'_096FDFB8-2692-D811-F483-553D578399F2',
# #                         u'subRegionName': u'DPV'},
# #                        {u'modelId': u'_9CE150A8-8CC5-A0F9-B67E-BBD8C79D3095',
# #                         u'modelName': u'sourceckt',
# #                         u'regionId': u'_79C9D814-3CE0-DC11-534D-BDA1AF949810',
# #                         u'regionName': u'PNNL',
# #                         u'stationId': u'_933D85C1-BE1C-4C05-D4DD-4B41D941C52C',
# #                         u'stationName': u'sourceckt_Substation',
# #                         u'subRegionId': u'_656EE259-23FF-086E-1DC0-39CB9DC60A20',
# #                         u'subRegionName': u'Taxonomy'}
#
# def timestep(data):
#     pprint(data)
#
# def test_model_retrieval():
#
#     gapps = GridAPPSD()
#     request = {"configurationType":"CIM Dictionary","parameters":{"model_id":"_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62"}}
#     #response = gapps.get_response("goss.gridappsd.process.request.config", json.dumps(request))
#     #response = gapps.query_model_info()
#     simulation = Simulation(gapps, run_config_123)
#     simulation.add_timestep_callback(timestep)
#     simulation.start_simulation()
#
#     i= 0
#     while i< 60:
#         time.sleep(1)
#         i+=1
#     #pprint(response)
