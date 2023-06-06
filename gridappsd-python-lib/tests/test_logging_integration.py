# import os
# import time

# import mock
# import pytest

# from gridappsd import GridAPPSD, topics as t
# from gridappsd.loghandler import Logger


# @pytest.fixture
# def logger_and_gridapspd(gridappsd_client) -> (Logger, GridAPPSD):

#     logger = Logger(gridappsd_client)

#     yield logger, gridappsd_client

#     logger = None


# @mock.patch.dict(os.environ,
#                  dict(GRIDAPPSD_APPLICATION_ID='sample_app',
#                       GRIDAPPSD_APPLICATION_STATUS='RUNNING'))
# def test_log_stored(logger_and_gridapspd):
#     logger, gapps = logger_and_gridapspd

#     log_data_map = [
#         (logger.debug, "A debug message", "DEBUG"),
#         (logger.info, "An info message", "INFO"),
#         (logger.error, "An error message", "ERROR"),
#         (logger.error, "Another error message", "ERROR"),
#         (logger.info, "Another info message", "INFO"),
#         (logger.debug, "A debug message", "DEBUG")
#     ]

#     assert gapps.connected

#     # Make the calls to debug
#     for d in log_data_map:
#         d[0](d[1])

#     payload = {
#         "query": "select * from log order by timestamp"
#     }
#     time.sleep(5)
#     response = gapps.get_response(t.LOGS, payload, timeout=60)
#     assert response['data'], "There were not any records returned."

#     for x in response['data']:
#         if x['source'] != 'sample_app':
#             continue
#         expected = log_data_map.pop(0)
#         assert expected[1] == x['log_message']
#         assert expected[2] == x['log_level']


# SIMULATION_ID='54321'

#  #TODO Ask about loging api for simulations.
# @mock.patch.dict(os.environ,
#                  dict(GRIDAPPSD_APPLICATION_ID='new_sample_app',
#                       GRIDAPPSD_APPLICATION_STATUS='RUNNING',
#                       GRIDAPPSD_SIMULATION_ID=SIMULATION_ID))
# def test_simulation_log_stored(logger_and_gridapspd):
#     logger, gapps = logger_and_gridapspd

#     assert gapps.get_simulation_id() == SIMULATION_ID

#     log_data_map = [
#         (logger.debug, "A debug message", "DEBUG"),
#         (logger.info, "An info message", "INFO"),
#         (logger.error, "An error message", "ERROR"),
#         (logger.error, "Another error message", "ERROR"),
#         (logger.info, "Another info message", "INFO"),
#         (logger.debug, "A debug message", "DEBUG")
#     ]

#     assert gapps.connected

#     # Make the calls to debug
#     for d in log_data_map:
#         d[0](d[1])

#     time.sleep(5)
#     payload = {
#         "query": "select * from log"
#     }

#     response = gapps.get_response(t.LOGS, payload, timeout=60)
#     assert response['data'], "There were not any records returned."

#     for x in response['data']:
#         if x['source'] != 'new_sample_app':
#             continue
#         expected = log_data_map.pop(0)
#         assert expected[1] == x['log_message']
#         assert expected[2] == x['log_level']
