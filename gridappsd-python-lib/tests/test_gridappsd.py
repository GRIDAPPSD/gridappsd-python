# import logging
# import os
# import xml.etree.ElementTree as ET
# from time import sleep

# import mock

from gridappsd import GridAPPSD, ProcessStatusEnum

#, topics as t


def _make_gappsd():
    return GridAPPSD(attempt_connection=False, username="u", password="p")


class TestApplicationAndServiceStatusShareState:
    """Unit coverage for the semantics the commented out test_gridappsd_status
    integration stub below documents: set_application_status and
    set_service_status both mutate the same shared _process_status field,
    and an invalid status string is silently ignored (with a warning), not
    raised, leaving the old value in place. No live broker is required:
    GridAPPSD is constructed with attempt_connection=False.
    """

    def test_starts_in_starting_status(self):
        gappsd = _make_gappsd()

        assert gappsd.get_application_status() == ProcessStatusEnum.STARTING.value
        assert gappsd.get_service_status() == ProcessStatusEnum.STARTING.value

    def test_set_application_status_is_visible_through_service_status(self):
        gappsd = _make_gappsd()

        gappsd.set_application_status("RUNNING")

        assert gappsd.get_service_status() == ProcessStatusEnum.RUNNING.value
        assert gappsd.get_application_status() == ProcessStatusEnum.RUNNING.value

    def test_set_service_status_is_visible_through_application_status(self):
        gappsd = _make_gappsd()

        gappsd.set_service_status("COMPLETE")

        assert gappsd.get_service_status() == ProcessStatusEnum.COMPLETE.value
        assert gappsd.get_application_status() == ProcessStatusEnum.COMPLETE.value

    def test_invalid_service_status_is_ignored_and_retains_old_value(self, monkeypatch):
        # The except ValueError branch in _set_status logs a warning, and the
        # logger reads GRIDAPPSD_APPLICATION_ID to build the log record. In
        # production app_registration.py sets this before app code runs; here
        # it must be set explicitly so the warning path itself does not raise.
        monkeypatch.setenv("GRIDAPPSD_APPLICATION_ID", "test-app-id")
        gappsd = _make_gappsd()
        gappsd.set_service_status("COMPLETE")

        gappsd.set_service_status("Foo")

        assert gappsd.get_service_status() == ProcessStatusEnum.COMPLETE.value
        assert gappsd.get_application_status() == ProcessStatusEnum.COMPLETE.value

    def test_invalid_application_status_is_ignored_and_retains_old_value(self, monkeypatch):
        monkeypatch.setenv("GRIDAPPSD_APPLICATION_ID", "test-app-id")
        gappsd = _make_gappsd()
        gappsd.set_application_status("RUNNING")

        gappsd.set_application_status("NotAValidStatus")

        assert gappsd.get_application_status() == ProcessStatusEnum.RUNNING.value


    # def test_get_gridappsd_client(gridappsd_client: GridAPPSD):
    #     assert isinstance(gridappsd_client, GridAPPSD)

    # def test_get_model_info(gridappsd_client):
    #     """ The expecation is that we will have multiple models that we can retrieve from the
    #     database.  Two of which should have the model name of ieee8500 and ieee123.  The models
    #     should have the correct entry keys.
    #     """

    #     gappsd = gridappsd_client
    #     import time
    #     time.sleep(10)
    #     info = gappsd.query_model_info()

    #     node_8500 = None
    #     node_123 = None
    #     for info_def in info['data']['models']:
    #         if info_def['modelName'] == 'ieee8500':
    #             node_8500 = info_def
    #         elif info_def['modelName'] == 'ieee123':
    #             node_123 = info_def

    #     assert node_123, "Missing the 123 model"
    #     assert node_8500, "Missing 8500 node model."

    #     keys = ["modelName", "modelId", "stationName", "stationId", "subRegionName", "subRegionId",
    #             "regionName", "regionId"]
    #     correct_keys = set(keys)

    #     assert len(correct_keys) == len(node_123)
    #     assert len(correct_keys) == len(node_8500)

    #     for x in node_123:
    #         correct_keys.remove(x)

    #     assert len(correct_keys) == 0

    #     correct_keys = set(keys)

    #     for x in node_8500:
    #         correct_keys.remove(x)

    #     assert len(correct_keys) == 0

    # def test_listener_multi_topic(gridappsd_client):
    #     gappsd = gridappsd_client

    #     class Listener:
    #         def __init__(self):
    #             self.call_count = 0

    #         def reset(self):
    #             self.call_count = 0

    #         def on_message(self, headers, message):
    #             print("Message was: {}".format(message))
    #             self.call_count += 1

    #     listener = Listener()

    #     input_topic = t.simulation_input_topic("5144")
    #     output_topic = t.simulation_output_topic("5144")

    #     gappsd.subscribe(input_topic, listener)
    #     gappsd.subscribe(output_topic, listener)

    #     gappsd.send(input_topic, "Any message")
    #     sleep(1)
    #     assert 1 == listener.call_count
    #     listener.reset()
    #     gappsd.send(output_topic, "No big deal")
    #     sleep(1)
    #     assert 1 == listener.call_count

    # @mock.patch.dict(os.environ, {"GRIDAPPSD_APPLICATION_ID": "helics_goss_bridge.py",
    #                               "GRIDAPPSD_SIMULATION_ID": "1234"})
    # def test_send_simulation_status_integration(gridappsd_client: GridAPPSD):

    #     class Listener:
    #         def __init__(self):
    #             self.call_count = 0

    #         def reset(self):
    #             self.call_count = 0

    #         def on_message(self, headers, message):
    #             print("Message was: {}".format(message))
    #             self.call_count += 1

    #     listener = Listener()
    #     gappsd = gridappsd_client
    #     assert os.environ['GRIDAPPSD_SIMULATION_ID'] == '1234'
    #     assert gappsd.get_simulation_id() == "1234"

    #     log_topic = t.simulation_log_topic(gappsd.get_simulation_id())
    #     gappsd.subscribe(log_topic, listener)
    #     gappsd.send_simulation_status("RUNNING",
    #         "testing the sending and recieving of send_simulation_status().",
    #         logging.DEBUG)
    #     sleep(1)
    #     assert listener.call_count == 1

    #     new_log_topic = t.simulation_log_topic("54232")
    #     gappsd.set_simulation_id(54232)
    #     gappsd.subscribe(new_log_topic, listener)
    #     gappsd.send_simulation_status(ProcessStatusEnum.COMPLETE.value, "Complete")
    #     sleep(1)
    #     assert listener.call_count == 2

    # @mock.patch.dict(os.environ, {"GRIDAPPSD_APPLICATION_ID": "helics_goss_bridge.py"})
    # def test_gridappsd_status(gridappsd_client):
    #     gappsd = gridappsd_client
    #     assert "helics_goss_bridge.py" == gappsd.get_application_id()
    #     assert gappsd.get_application_status() == ProcessStatusEnum.STARTING.value
    #     assert gappsd.get_service_status() == ProcessStatusEnum.STARTING.value
    #     gappsd.set_application_status("RUNNING")

    #     assert gappsd.get_service_status() == ProcessStatusEnum.RUNNING.value
    #     assert gappsd.get_application_status() == ProcessStatusEnum.RUNNING.value

    #     gappsd.set_service_status("COMPLETE")
    #     assert gappsd.get_service_status() == ProcessStatusEnum.COMPLETE.value
    #     assert gappsd.get_application_status() == ProcessStatusEnum.COMPLETE.value

    #     # Invalid
    #     gappsd.set_service_status("Foo")
    #     assert gappsd.get_service_status() == ProcessStatusEnum.COMPLETE.value
    #     assert gappsd.get_application_status() == ProcessStatusEnum.COMPLETE.value
