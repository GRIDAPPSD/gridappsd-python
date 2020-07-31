import os

import mock
import pytest

from gridappsd import GridAPPSD
from gridappsd.loghandler import Logger


@pytest.fixture
def logger_and_gridapspd(gridappsd_client):

    logger = Logger(gridappsd_client)

    yield logger, gridappsd_client

    logger = None


@mock.patch.dict(os.environ,
                 dict(GRIDAPPSD_APPLICATION_ID='sample_app',
                      GRIDAPPSD_SIMULATION_ID='1203',
                      GRIDAPPSD_APPLICATION_STATUS='RUNNING'))
def test_log_stored(logger_and_gridapspd):
    logger, gapps = logger_and_gridapspd

    logger.debug("This should get called to the log")
