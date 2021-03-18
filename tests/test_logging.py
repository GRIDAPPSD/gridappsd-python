from gridappsd.loghandler import Logger
from gridappsd import topics as t, ProcessStatusEnum
import os
import mock
from mock import Mock
import pytest


def init_gapps_mock(simulation_id=None, application_id=None, process_status=None, service_id=None):
    gapps = Mock()

    gapps.get_simulation_id.return_value = simulation_id
    gapps.get_application_id.return_value = application_id
    gapps.get_application_status.return_value = process_status
    gapps.get_process_id.return_value = service_id

    return gapps


#@mock.patch('gridappsd.utils.get_application_id')
def test_required_application_id_set():
    """ os.environ['GRIDAPPSD_APPLICATION_ID'] must be set to run."""
    log = Logger(init_gapps_mock())

    with pytest.raises(AttributeError):
        log.debug("foo")


def test_no_simulation_id_topic_or_application_id():
    """If no simulation then the topic should be the platform log topic"""
    expected_topic = t.platform_log_topic()

    gapps_mock = init_gapps_mock(application_id="my_app_id",
                                 process_status=ProcessStatusEnum.STARTING.value)
    log = Logger(gapps_mock)

    log.debug("A message")

    topic, message = gapps_mock.send.call_args.args

    assert expected_topic == topic
    assert message['processStatus']  == ProcessStatusEnum.STARTING.value
    assert message['logMessage'] == 'A message'


def test_platform_log():

    application_id = "my_app"
    gapps_mock = init_gapps_mock(application_id=application_id, process_status=ProcessStatusEnum.STOPPING.value)
    log = Logger(gapps_mock)

    log.debug("foo")
    gapps_mock.send.assert_called_once()

    # send should have been passed a topic and a message
    topic, message = gapps_mock.send.call_args.args

    assert message['source'] == application_id
    assert message['logLevel'] == 'DEBUG'
    assert message['logMessage'] == 'foo'
    assert message['processStatus'] == ProcessStatusEnum.STOPPING.value
    gapps_mock.send.reset_mock()

    log.info("bar")
    gapps_mock.send.assert_called_once()
    # send should have been passed a topic and a message
    topic, message = gapps_mock.send.call_args.args
    assert application_id == message['source']
    assert 'INFO' == message['logLevel']
    assert 'bar' == message['logMessage']
    gapps_mock.send.reset_mock()

    log.error("bim")
    gapps_mock.send.assert_called_once()
    # send should have been passed a topic and a message
    topic, message = gapps_mock.send.call_args.args
    assert application_id == message['source']
    assert 'ERROR' == message['logLevel']
    assert 'bim' == message['logMessage']
    gapps_mock.send.reset_mock()

    log.warning("baf")
    gapps_mock.send.assert_called_once()
    # send should have been passed a topic and a message
    topic, message = gapps_mock.send.call_args.args
    assert application_id == message['source']
    assert 'WARN' == message['logLevel']
    assert 'baf' == message['logMessage']


def test_invalid_log_level():
    application_id = "my_app"
    gapps_mock = init_gapps_mock(application_id=application_id, process_status=ProcessStatusEnum.STOPPING.value)
    log = Logger(gapps_mock)

    with pytest.raises(AttributeError):
        log.log("junk error", "BART")


def test_topic_and_status_set_correctly():

    sim_id = "543"
    application_id = "wicked_good_app_id"
    mock_gapps = init_gapps_mock(simulation_id=sim_id, application_id=application_id,
                                 process_status=ProcessStatusEnum.RUNNING.value)

    expected_topic = t.simulation_log_topic(sim_id)

    log = Logger(mock_gapps)

    log.debug("A message")

    # During the call to debug we expect the send function to be
    # called on the mock object.  Grab the arguments and then
    # make sure that they are what we expect.
    topic, message = mock_gapps.send.call_args.args

    assert message['source'] == application_id
    assert topic == expected_topic
    assert message['processStatus'] == "RUNNING"


