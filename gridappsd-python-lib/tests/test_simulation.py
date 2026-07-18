import json
import logging
import os
import sys
import time
import pytest
from datetime import datetime, timezone

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

from gridappsd import GridAPPSD, topics as t
from gridappsd.simulation import Simulation, PowerSystemConfig, SimulationArgs, SimulationConfig

simulation_is_complete = False
measurements_received = 0

@pytest.fixture
def createGadObject():
    gad_user = os.environ.get('GRIDAPPSD_USER')
    if gad_user is None:
        os.environ['GRIDAPPSD_USER'] = 'system'
    gad_password = os.environ.get('GRIDAPPSD_PASSWORD')
    if gad_password is None:
        os.environ['GRIDAPPSD_PASSWORD'] = 'manager'
    return GridAPPSD()

@pytest.mark.integration
def test_createSimulations(createGadObject):
    gadObj = createGadObject
    response = gadObj.query_model_info()
    models = response.get("data", {}).get("models", {})
    start_time = int(datetime(year=2025,
                              month=1,
                              day=1,
                              hour=0,
                              minute=0,
                              second=0,
                              microsecond=0,
                              tzinfo=timezone.utc).timestamp())
    simulationArgs = SimulationArgs(start_time=start_time,
                                    duration=300,
                                    run_realtime=False,
                                    interval=60,
                                    publish_period=120,
                                    pause_after_measurements=False)
    sim_config = SimulationConfig(simulation_config=simulationArgs)
    modelsToRun = [
        "49AD8E07-3BF9-A4E2-CB8F-C3722F837B62", # IEEE 13 Node Test Feeder contains 175 measurements
        "C1C3E687-6FFD-C753-582B-632A27E28507", # IEEE 123 Node Test Feeder contains 782 measurements
        "5B816B93-7A5F-B64C-8460-47C17D6E4B0F"  # IEEE 13  Node Assets Test Feeder contains 127 measurements
    ]
    for m in models:
        if m.get("modelId") not in modelsToRun:
            continue
        line_name = m.get("modelId")
        subregion_name = m.get("subRegionId")
        region_name = m.get("regionId")
        psc = PowerSystemConfig(Line_name=line_name,
                                SubGeographicalRegion_name=subregion_name,
                                GeographicalRegion_name=region_name)
        sim_config.power_system_configs.append(psc)
    sim_obj = Simulation(gapps=gadObj, run_config=sim_config)
    def on_measurement(sim, ts, m):
        global measurements_received
        assert len(m) == 1084
        measurements_received += 1
    def on_simulation_complete(sim):
        global simulation_is_complete
        simulation_is_complete = True
    sim_obj.add_onmeasurement_callback(on_measurement)
    sim_obj.add_oncomplete_callback(on_simulation_complete)
    sim_obj.start_simulation()
    while not simulation_is_complete:
        time.sleep(1)
    assert measurements_received == 2
    gadObj.disconnect()
