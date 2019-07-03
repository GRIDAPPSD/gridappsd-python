from gridappsd.loghandler import Logger
from gridappsd import topics as t
import os
import mock
from mock import Mock
import pytest


@pytest.fixture
def logger_mock():
    gapps = Mock()
    log = Logger(gapps)

    yield gapps, log

    gapps = None
    log = None


def test_required_application_id_set(logger_mock):
    """ os.environ['GRIDAPPSD_APPLICATION_ID'] must be set to run."""
    gapps, log = logger_mock

    with pytest.raises(AttributeError):
        log.debug("foo")


@mock.patch.dict(os.environ,
                 dict(GRIDAPPSD_APPLICATION_ID='test_log_levels',
                      GRIDAPPSD_APPLICATION_STATUS="STOPPED"))
def test_no_simulation_id_topic_or_application_id(logger_mock):
    """If no simulation then the topic should be the platform log topic"""

    expected_topic = t.platform_log_topic()

    gapps, log = logger_mock

    log.debug("A message")

    topic, message = gapps.send.call_args.args

    assert expected_topic == topic
    assert 'STOPPED' == message['processStatus']


GRIDAPPSD_SIMULATION_ID = "541"


@mock.patch.dict(os.environ, dict(GRIDAPPSD_APPLICATION_ID='test_log_levels',
                                  GRIDAPPSD_SIMULATION_ID=GRIDAPPSD_SIMULATION_ID,
                                  GRIDAPPSD_APPLICATION_STATUS="ERROR"))
def test_log(logger_mock):

    gapps, log = logger_mock

    log.debug("foo")
    gapps.send.assert_called_once()

    # send should have been passed a topic and a message
    topic, message = gapps.send.call_args.args
    assert 'test_log_levels' == message['source']
    assert 'DEBUG' == message['logLevel']
    assert 'foo' == message['logMessage']
    assert 'ERROR' == message['processStatus']
    gapps.send.reset_mock()

    log.info("bar")
    gapps.send.assert_called_once()
    # send should have been passed a topic and a message
    topic, message = gapps.send.call_args.args
    assert 'test_log_levels' == message['source']
    assert 'INFO' == message['logLevel']
    assert 'bar' == message['logMessage']
    gapps.send.reset_mock()

    log.error("bim")
    gapps.send.assert_called_once()
    # send should have been passed a topic and a message
    topic, message = gapps.send.call_args.args
    assert 'test_log_levels' == message['source']
    assert 'ERROR' == message['logLevel']
    assert 'bim' == message['logMessage']
    gapps.send.reset_mock()

    log.warning("baf")
    gapps.send.assert_called_once()
    # send should have been passed a topic and a message
    topic, message = gapps.send.call_args.args
    assert 'test_log_levels' == message['source']
    assert 'WARNING' == message['logLevel']
    assert 'baf' == message['logMessage']


@mock.patch.dict(os.environ,
                 dict(GRIDAPPSD_APPLICATION_ID='test_log_levels',
                      GRIDAPPSD_SIMULATION_ID=GRIDAPPSD_SIMULATION_ID,
                      GRIDAPPSD_APPLICATION_STATUS="RUNNING"))
def test_topic_and_status_set_correctly(logger_mock):

    expected_topic = t.simulation_log_topic(GRIDAPPSD_SIMULATION_ID)

    gapps, log = logger_mock

    log.debug("A message")

    topic, message = gapps.send.call_args.args

    assert expected_topic == topic
    assert "RUNNING" == message['processStatus']


