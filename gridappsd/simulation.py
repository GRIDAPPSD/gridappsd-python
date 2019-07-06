import json
import sys
import time

from . topics import simulation_input_topic, simulation_output_topic, simulation_log_topic


class Simulation(object):
    def __init__(self, gapps, simulation_id, duration, timestep_finished=None):
        self.gappsd = gapps
        self.simulation_id = simulation_id
        self._show_timesteps = True
        self._duration = int(duration)
        self._timestep_requested = 0
        self._timestep_finished_callback = timestep_finished
        self._is_running = True
        self.gappsd.subscribe(simulation_log_topic(simulation_id), self._on_message)

    def _on_message(self, headers, message):
        if 'logMessage' in message:
            log_message = message['logMessage']
            if log_message.startswith("done with timestep"):
                timestep = int(log_message[len("done with timestep "):])
                if self._timestep_finished_callback is not None:
                    self._timestep_finished_callback(self, timestep)
                # We use -1 here because the last timestep from fncs-goss-bridge.py never actually
                # comes through at least as of 2019-6-7
                if timestep >= self._duration-1:
                    self._is_running = False

        if self._show_timesteps:
            # print(headers, message)
            # print(headers)
            sys.stdout.write("{}\n".format(message['logMessage']))
            # print(message["logMessage"])

    @property
    def running(self):
        return self.is_running()

    @property
    def showing_status(self):
        return self._show_timesteps

    def pause(self):
        """Pause simulation"""
        command = dict(command="pause")
        self.gappsd.send(simulation_input_topic(self.simulation_id), json.dumps(command))

    def stop(self):
        """Stop the simulation"""
        command = dict(command="stop")
        self.gappsd.send(simulation_input_topic(self.simulation_id), json.dumps(command))

    def resume(self):
        """Resume the simulation"""
        command = dict(command="resume")
        self.gappsd.send(simulation_input_topic(self.simulation_id), json.dumps(command))

    def simulation_main_loop(self):

        while self._is_running:
            time.sleep(0.1)