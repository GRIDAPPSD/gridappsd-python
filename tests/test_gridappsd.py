import os
from time import sleep

import mock

from mock import call, patch, PropertyMock

from gridappsd.goss import GOSS
from gridappsd import GridAPPSD, topics, ProcessStatusEnum
import pytest


def test_get_model_info(gridappsd_client):
    """ The expecation is that we will have multiple models that we can retrieve from the
    database.  Two of which should have the model name of ieee8500 and ieee123.  The models
    should have the correct entry keys.
    """
    gappsd = gridappsd_client

    info = gappsd.query_model_info()

    node_8500 = None
    node_123 = None
    for info_def in info['data']['models']:
        if info_def['modelName'] == 'ieee8500':
            node_8500 = info_def
        elif info_def['modelName'] == 'ieee123':
            node_123 = info_def

    assert node_123, "Missing the 123 model"
    assert node_8500, "Missing 8500 node model."

    keys = ["modelName", "modelId", "stationName", "stationId", "subRegionName", "subRegionId",
            "regionName", "regionId"]
    correct_keys = set(keys)

    assert len(correct_keys) == len(node_123)
    assert len(correct_keys) == len(node_8500)

    for x in node_123:
        correct_keys.remove(x)

    assert len(correct_keys) == 0

    correct_keys = set(keys)

    for x in node_8500:
        correct_keys.remove(x)

    assert len(correct_keys) == 0


def test_listener_multi_topic(gridappsd_client):
    gappsd = gridappsd_client

    class Listener:
        def __init__(self):
            self.call_count = 0

        def reset(self):
            self.call_count = 0

        def on_message(self, headers, message):
            print("Message was: {}".format(message))
            self.call_count += 1

    listener = Listener()

    input_topic = topics.simulation_input_topic("5144")
    output_topic = topics.simulation_output_topic("5144")

    gappsd.subscribe(input_topic, listener)
    gappsd.subscribe(output_topic, listener)

    gappsd.send(input_topic, "Any message")
    sleep(1)
    assert 1 == listener.call_count
    listener.reset()
    gappsd.send(output_topic, "No big deal")
    sleep(1)
    assert 1 == listener.call_count
    

@patch.object(GOSS,"__init__", return_value=None)
@patch('gridappsd.datetime')
@patch.object(GOSS,"send")   
def test_build_message_json(mock_datetime,mock_goss_send,mock_goss_init):
    os.environ["GRIDAPPSD_APPLICATION_ID"] = "helics_goss_bridge.py"
    mock_datetime.utcnow.return_value = datetime(2017,8,25,10,33,6,150642)
    t_now = mock_datetime.utcnow()
    gad = GridAPPSD(simulation_id="1234")
    gad.send_simulation_status("RUNNING",
        "testing build_message_json().", 
        "INFO")
    log_msg_dict = {
        "source": "helics_goss_bridge.py",
        "processId": str(gad.get_simulation_id()),
        "timestamp": int(time.mktime(t_now.timetuple()))*1000,
        "processStatus": "RUNNING",
        "logMessage": "testing build_message_json().",
        "logLevel": "INFO",
        "storeToDb": True
    }
    log_topic = topics.simulation_log_topic(gappds.get_simulation_id())
    mock_goss_send.assert_called_once_with(log_topic, json.dumps(log_msg_dict))
    

@mock.patch.dict(os.environ, {"GRIDAPPSD_APPLICATION_ID": "helics_goss_bridge.py",
                              "GRIDAPPSD_SIMULATION_ID": "1234"})
def test_send_simulation_status_integration(gridappsd_client: GridAPPSD):

    class Listener:
        def __init__(self):
            self.call_count = 0

        def reset(self):
            self.call_count = 0

        def on_message(self, headers, message):
            print("Message was: {}".format(message))
            self.call_count += 1

    listener = Listener()
    gappsd = gridappsd_client
    assert os.environ['GRIDAPPSD_SIMULATION_ID'] == '1234'
    assert gappsd.get_simulation_id() == "1234"

    log_topic = topics.simulation_log_topic(gappsd.get_simulation_id())
    gappsd.subscribe(log_topic, listener)
    gappsd.send_simulation_status("RUNNING",
        "testing the sending and recieving of send_simulation_status().", 
        "INFO")
    sleep(1)
    assert listener.call_count == 1

    new_log_topic = topics.simulation_log_topic("54232")
    gappsd.set_simulation_id(54232)
    gappsd.subscribe(new_log_topic, listener)
    gappsd.send_simulation_status(ProcessStatusEnum.COMPLETE.value, "Complete")
    sleep(1)
    assert listener.call_count == 2



@mock.patch.dict(os.environ, {"GRIDAPPSD_APPLICATION_ID": "helics_goss_bridge.py"})
def test_gridappsd_status(gridappsd_client):
    gappsd = gridappsd_client
    assert "helics_goss_bridge.py" == gappsd.get_application_id()
    assert gappsd.get_application_status() == ProcessStatusEnum.STARTING.value
    assert gappsd.get_service_status() == ProcessStatusEnum.STARTING.value
    gappsd.set_application_status("RUNNING")

    assert gappsd.get_service_status() == ProcessStatusEnum.RUNNING.value
    assert gappsd.get_application_status() == ProcessStatusEnum.RUNNING.value

    gappsd.set_service_status("COMPLETE")
    assert gappsd.get_service_status() == ProcessStatusEnum.COMPLETE.value
    assert gappsd.get_application_status() == ProcessStatusEnum.COMPLETE.value

    # Invalid
    gappsd.set_service_status("Foo")
    assert gappsd.get_service_status() == ProcessStatusEnum.COMPLETE.value
    assert gappsd.get_application_status() == ProcessStatusEnum.COMPLETE.value
