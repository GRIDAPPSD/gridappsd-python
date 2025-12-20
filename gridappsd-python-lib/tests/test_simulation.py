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

@pytest.fixture
def createGadObject():
    gad_user = os.environ.get('GRIDAPPSD_USER')
    if gad_user is None:
        os.environ['GRIDAPPSD_USER'] = 'system'
    gad_password = os.environ.get('GRIDAPPSD_PASSWORD')
    if gad_password is None:
        os.environ['GRIDAPPSD_PASSWORD'] = 'manager'
    return GridAPPSD()


def test_createSimulations(createGadObject):
    gadObj = createGadObject
    response = gadObj.query_model_info()
    models = response.get("data", {}).get("models", {})
    start_time = int(datetime(year=2025, month=1, day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc).timestamp())
    simulationArgs = SimulationArgs(start_time=f"{start_time}",
                                    duration="120",
                                    run_realtime=True,
                                    pause_after_measurements=False)
    sim_config = SimulationConfig(simulation_config=simulationArgs)
    for m in models:
        line_name = m.get("modelId")
        subregion_name = m.get("subRegionId")
        region_name = m.get("regionId")
        psc = PowerSystemConfig(Line_name=line_name,
                                SubGeographicalRegion_name=subregion_name,
                                GeographicalRegion_name=region_name)
        sim_config.power_system_configs.append(psc)
    sim_obj = Simulation(gapps=gadObj, run_config=sim_config)
    rvStr = json.dumps(sim_obj._run_config, indent=4, sort_keys=True)
    pass