import time
from copy import deepcopy
import json
import logging

from . import topics as t
from .topics import simulation_input_topic

_log = logging.getLogger(__name__)


class SimulationFailedToStartError(Exception):
    """Exception raised if a simulation fails to start."""
    pass


class Simulation(object):
    """ Simulation object allows controlling simulations through a python API.

    The simulation object allows controlling and monitoring of simulations through
    a python API.  It is capable of starting, stopping, pausing and restarting simulations
    that are run on GridAPPSD.

    There are four events that can be registered: ontimestep, onmeasurement, oncomplete, and
    onstart.  To register one of the events call the method add_ontimestep_callback,
    add_onmeasurement_callback, add_oncomplete_callback or add_onstart_callback method respectively.
    """
    def __init__(self, gapps: 'GridAPPSD', run_config):
        assert type(gapps).__name__ == 'GridAPPSD',  "Must be an instance of GridAPPSD"
        assert isinstance(run_config, dict)
        self._gapps = gapps
        self._run_config = deepcopy(run_config)
        self._running_or_paused = False

        # Will be populated when the simulation is first started.
        self.simulation_id = None

        self.__on_start = set()
        self.__on_next_timestep_callbacks = set()
        self.__on_simulation_complete_callbacks = set()

        self._measurement_count = 0
        self._log_count = 0
        self._platform_log_count = 0

        self._num_timesteps = round(float(run_config['simulation_config']['duration']))

        # Devices that the user wants measurements from
        self._device_measurement_filter = {}

        self.__filterable_measurement_callback_set = set()

    def start_simulation(self, timeout=30):
        """ Start the configured simulation by calling the REQUEST_SIMULATION endpoint.
        """
        resp = self._gapps.get_response(t.REQUEST_SIMULATION, json.dumps(self._run_config), timeout=timeout)

        if 'simulationId' not in resp:
            message = "Simulation was not able to run\n" + str(resp)
            raise SimulationFailedToStartError(message)

        self._running_or_paused = True
        self.simulation_id = resp['simulationId']

        # Subscribe to the different components necessary to run and receive
        # simulated measurements and messages.
        self._gapps.subscribe(t.simulation_log_topic(self.simulation_id), self.__on_simulation_log)
        self._gapps.subscribe(t.simulation_output_topic(self.simulation_id), self.__onmeasurement)
        self._gapps.subscribe(t.platform_log_topic(), self.__on_platformlog)

        for p in self.__on_start:
            p(self)

    def pause(self):
        """ Pause simulation"""
        _log.debug("Pausing simulation")
        command = dict(command="pause")
        self._gapps.send(simulation_input_topic(self.simulation_id), json.dumps(command))
        self._running_or_paused = True

    def stop(self):
        """ Stop the simulation"""
        _log.debug("Stopping simulation")
        command = dict(command="stop")
        self._gapps.send(simulation_input_topic(self.simulation_id), json.dumps(command))
        self._running_or_paused = True

    def resume(self):
        """ Resume the simulation"""
        _log.debug("Resuming simulation")
        command = dict(command="resume")
        self._gapps.send(simulation_input_topic(self.simulation_id), json.dumps(command))
        self._running_or_paused = True

    def run_loop(self):
        """ Loop around the running of the simulation itself.

        Example:

            gapps = GridAPPSD()

            # Create simulation object.
            simulation = Simulation(gapps, config)
            simulation.add_ontimestep_callback(ontimestep)
            simulation.add_oncomplete_callback(oncomplete)
            simulation.add_onmeasurement_callback(onmeasurment)
            simulation.add_onstart_callback(onstart)
            simulation.run_loop()

        """
        if not self._running_or_paused:
            _log.debug("Running simulation in loop until simulation is done.")
            self.start_simulation()

        while self._running_or_paused:
            time.sleep(0.01)

    def resume_pause_at(self, pause_in):
        """ Resume the simulation and have it automatically pause after specified amount of seconds later.
        
        :param pause_in: number of seconds to run before pausing the simulation
        """
        _log.debug("Resuming simulation. Will pause after {} seconds".format(pause_in))
        command = dict(command="resumePauseAt", input=dict(pauseIn=pause_in))
        self._gapps.send(simulation_input_topic(self.simulation_id), json.dumps(command))
        self._running_or_paused = True

    def add_onmeasurement_callback(self, callback, device_filter=()):
        """ registers an onmeasurment callback to be called when measurements have come through.

        Note:

            The device_filter has not been fully implemented at present!

        The callback parameter must be a function that takes three arguments (the simulation object,
        a timstep and a measurement dictionary)

        Callback Example:

            def onmeasurment(sim, timestep, measurements):
                print("timestep: {}, measurement: {}".format(timestep, measurements))

        :param callback: Function to be called during running of simulation
        :param device_filter: Future filter of measurements
        :return:
        """
        self.__filterable_measurement_callback_set.add((callback, device_filter))

    def add_onstart_callback(self, callback):
        """ registers a start callback that is called when the simulation is started

        Callback Example:

            def onstart(sim):
                print("Sim started: {}".format(sim.simulation_id))



        :param callback:
        :return:
        """
        self.__on_start.add(callback)

    def add_oncomplete_callback(self, callback):
        """ registers a completion callback when the last timestep has been requested.

        Callback Example:

            def onfinishsimulation(sim):
                print("Completed simulator")

        :param callback:
        :return:
        """
        self.__on_simulation_complete_callbacks.add(callback)

    def add_ontimestep_callback(self, callback):
        """ register a timestep callback

        Callback Example:

            def ontimestep(sim, timestep):
                print("Timestamp: {}".format(timestep))

        :param callback:
        :return:
        """
        self.__on_next_timestep_callbacks.add(callback)

    def __on_platformlog(self, headers, message):
        try:
            if self.simulation_id == message['processId']:
                _log.debug(f"__on_platform_log: message: {message}")
        except KeyError as e:
            _log.error(f"__on_platformlog keyerror({e}): {message}")

        if 'command' in message:
            _log.debug("Command was: {}".format(message))

    def __on_simulation_log(self, headers, message):
        # Handle the callbacks here
        if 'logMessage' in message:
            log_message = message['logMessage']
            # if this is the last timestamp then call the finished callbacks
            if log_message == f"Simulation {self.simulation_id} complete":
                for p in self.__on_simulation_complete_callbacks:
                    p(self)
                self._running_or_paused = False
                _log.debug("Simulation completed")
            elif log_message.startswith("incrementing to "):
                timestep = log_message[len("incrementing to "):]
                for p in self.__on_next_timestep_callbacks:
                    p(self, int(timestep))

    def __onmeasurement(self, headers, message):
        """ Call the measurement callbacks

        :param headers:
        :param message:
        :return:
        """
        sim_id = message['simulation_id']
        timestamp = message['message']['timestamp']
        measurements = message['message']['measurements']
        for p in self.__filterable_measurement_callback_set:
            p[0](self, timestamp, measurements)
