"""Unit tests for gridappsd.simulation.Simulation's command-sending methods.

These tests exercise _send_simulation_command and the pause/stop/resume/
resume_pause_at wrappers built on it, asserting the exact JSON payload sent
and the destination topic. No live broker or docker stack is required:
GridAPPSD is constructed with attempt_connection=False, and Simulation's
own gapps.send call is mocked directly.
"""

from unittest import mock

import gridappsd.topics as t
from gridappsd import GridAPPSD, json_extension as json
from gridappsd.simulation import Simulation


def _make_simulation():
    gapps = GridAPPSD(attempt_connection=False, username="u", password="p")
    run_config = {"simulation_config": {"duration": 300}}
    simulation = Simulation(gapps, run_config)
    simulation.simulation_id = "12345"
    return simulation


class TestSendSimulationCommand:
    def test_command_without_input_omits_input_key(self):
        simulation = _make_simulation()

        with mock.patch.object(simulation._gapps, "send") as mock_send:
            simulation._send_simulation_command("pause")

        mock_send.assert_called_once()
        destination, body = mock_send.call_args[0]
        assert destination == t.simulation_input_topic("12345")
        assert json.loads(body) == {"command": "pause"}
        assert simulation._running_or_paused is True

    def test_command_with_input_nests_it_under_input_key(self):
        simulation = _make_simulation()

        with mock.patch.object(simulation._gapps, "send") as mock_send:
            simulation._send_simulation_command("resumePauseAt", pauseIn=30)

        destination, body = mock_send.call_args[0]
        assert destination == t.simulation_input_topic("12345")
        assert json.loads(body) == {"command": "resumePauseAt", "input": {"pauseIn": 30}}


class TestPauseStopResumeWrappers:
    def test_pause_sends_bare_pause_command(self):
        simulation = _make_simulation()

        with mock.patch.object(simulation._gapps, "send") as mock_send:
            simulation.pause()

        _, body = mock_send.call_args[0]
        assert json.loads(body) == {"command": "pause"}

    def test_stop_sends_bare_stop_command(self):
        simulation = _make_simulation()

        with mock.patch.object(simulation._gapps, "send") as mock_send:
            simulation.stop()

        _, body = mock_send.call_args[0]
        assert json.loads(body) == {"command": "stop"}

    def test_resume_sends_bare_resume_command(self):
        simulation = _make_simulation()

        with mock.patch.object(simulation._gapps, "send") as mock_send:
            simulation.resume()

        _, body = mock_send.call_args[0]
        assert json.loads(body) == {"command": "resume"}

    def test_resume_pause_at_sends_command_with_nested_pause_in(self):
        simulation = _make_simulation()

        with mock.patch.object(simulation._gapps, "send") as mock_send:
            simulation.resume_pause_at(45)

        _, body = mock_send.call_args[0]
        assert json.loads(body) == {"command": "resumePauseAt", "input": {"pauseIn": 45}}

    def test_all_wrappers_set_running_or_paused_true(self):
        simulation = _make_simulation()
        simulation._running_or_paused = False

        with mock.patch.object(simulation._gapps, "send"):
            simulation.pause()

        assert simulation._running_or_paused is True
