from dataclasses import dataclass, field, fields
from pathlib import Path
import sys
import time
from copy import deepcopy
import json
import logging
from typing import Dict, List, Union

import gridappsd.topics as t

_log = logging.getLogger(__name__)


class SimulationFailedToStartError(Exception):
    """Exception raised if a simulation fails to start."""
    pass


@dataclass
class ConfigBase:

    def asjson(self):
        return json.dumps(self.asdict())

    def asdict(self):
        built = {}
        for k, v in self.__dict__.items():
            if isinstance(v, ConfigBase):
                built[k] = v.asdict()
            else:
                built[k] = v
        return built


@dataclass
class ModelCreationConfig(ConfigBase):
    load_scaling_factor: str = "1"
    schedule_name: str = "ieeezipload"
    z_fraction: str = "0"
    i_fraction: str = "1"
    p_fraction: str = "0"
    randomize_zipload_fractions: bool = False
    use_houses: bool = False


__default_model_creation_config__ = ModelCreationConfig()


@dataclass
class SimulationArgs(ConfigBase):
    start_time: str = "1655321830"
    duration: str = "300"
    simulator: str = "GridLAB-D"
    timestep_frequency: str = "1000"
    timestep_increment: str = "1000"
    run_realtime: bool = True
    simulation_name: str = "ieee13nodeckt"
    power_flow_solver_method: str = "NR"
    model_creation_config: ModelCreationConfig = __default_model_creation_config__


__default_simulation_args__ = SimulationArgs()


@dataclass
class Application(ConfigBase):
    pass


@dataclass
class ApplicationConfig(ConfigBase):
    applications: List[Application] = field(default_factory=list)


__default_application_config__ = ApplicationConfig()


@dataclass
class TestConfig(ConfigBase):
    events: List[Dict] = field(default_factory=list)
    appId: str = ""


__default_test_config__ = TestConfig()


@dataclass
class ServiceConfig(ConfigBase):
    pass


@dataclass
class PowerSystemConfig(ConfigBase):
    Line_name: str
    GeographicalRegion_name: str = None
    SubGeographicalRegion_name: str = None


@dataclass
class SimulationConfig(ConfigBase):
    power_system_config: PowerSystemConfig
    application_config: List[ApplicationConfig] = field(default_factory=list)
    simulation_config: SimulationArgs = __default_simulation_args__
    service_configs: List[ServiceConfig] = field(default_factory=list)
    application_config: ApplicationConfig = __default_application_config__
    test_config: TestConfig = __default_test_config__


class Simulation:
    """ Simulation object allows controlling simulations through a python API.

    The simulation object allows controlling and monitoring of simulations through
    a python API.  It is capable of starting, stopping, pausing and restarting simulations
    that are run on GridAPPSD.

    There are four events that can be registered: ontimestep, onmeasurement, oncomplete, and
    onstart.  To register one of the events call the method add_ontimestep_callback,
    add_onmeasurement_callback, add_oncomplete_callback or add_onstart_callback method respectively.
    """

    def __init__(self, gapps: 'GridAPPSD',
                 run_config: Union[Dict, SimulationConfig]):
        assert type(
            gapps).__name__ == 'GridAPPSD', "Must be an instance of GridAPPSD"

        self._run_config = run_config
        # if isinstance(run_config, SimulationConfig):
        #     self._run_config = run_config
        # else:
        #     psconfig = PowerSystemConfig(**run_config['power_system_config'])
        #     appconfig = ApplicationConfig(**run_config['application_config'])
        #     simconfig = SimulationConfig(**run_config["simulation_config"])
        #     testconfig = TestConfig(**run_config['test_config'])
        #     serviceconfig = ServiceConfig(**run_config['service_configs'])

        #     self._run_config = SimulationConfig(power_system_config=psconfig,
        #                                         application_config=appconfig,
        #                                         simulation_config=simconfig,
        #                                         service_configs=serviceconfig,
        #                                         test_config=testconfig)
        # print(self._run_config.asdict())
        # Path("asdict.json").write_text((json.dumps(self._run_config.asdict())))
        # sys.exit()
        self._gapps = gapps
        self._running_or_paused = False

        # Will be populated when the simulation is first started.
        self.simulation_id = None

        self.__on_start = set()
        self.__on_next_timestep_callbacks = set()
        self.__on_simulation_complete_callbacks = set()

        self._measurement_count = 0
        self._log_count = 0
        self._platform_log_count = 0

        self._num_timesteps = round(
            float(self._run_config["simulation_config"]["duration"]))

        # self._num_timesteps = round(
        #     float(self._run_config.simulation_config.duration))

        # Devices that the user wants measurements from
        self._device_measurement_filter = {}

        self.__filterable_measurement_callback_set = set()

    def start_simulation(self, timeout=30):
        """ Start the configured simulation by calling the REQUEST_SIMULATION endpoint.
        """
        resp = self._gapps.get_response(t.REQUEST_SIMULATION,
                                        self._run_config,
                                        timeout=timeout)

        if 'simulationId' not in resp:
            message = "Simulation was not able to run\n" + str(resp)
            raise SimulationFailedToStartError(message)

        self._running_or_paused = True
        self.simulation_id = resp['simulationId']

        # Subscribe to the different components necessary to run and receive
        # simulated measurements and messages.
        self._gapps.subscribe(t.simulation_log_topic(self.simulation_id),
                              self.__on_simulation_log)
        self._gapps.subscribe(t.simulation_output_topic(self.simulation_id),
                              self.__onmeasurement)
        self._gapps.subscribe(t.platform_log_topic(), self.__on_platformlog)

        for p in self.__on_start:
            p(self)

    def pause(self):
        """ Pause simulation"""
        _log.debug("Pausing simulation")
        command = dict(command="pause")
        self._gapps.send(t.simulation_input_topic(self.simulation_id),
                         json.dumps(command))
        self._running_or_paused = True

    def stop(self):
        """ Stop the simulation"""
        _log.debug("Stopping simulation")
        command = dict(command="stop")
        self._gapps.send(t.simulation_input_topic(self.simulation_id),
                         json.dumps(command))
        self._running_or_paused = True

    def resume(self):
        """ Resume the simulation"""
        _log.debug("Resuming simulation")
        command = dict(command="resume")
        self._gapps.send(t.simulation_input_topic(self.simulation_id),
                         json.dumps(command))
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
        _log.debug("Resuming simulation. Will pause after {} seconds".format(
            pause_in))
        command = dict(command="resumePauseAt", input=dict(pauseIn=pause_in))
        self._gapps.send(t.simulation_input_topic(self.simulation_id),
                         json.dumps(command))
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
        self.__filterable_measurement_callback_set.add(
            (callback, device_filter))

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


if __name__ == '__main__':
    from pprint import pprint
    psc = PowerSystemConfig(Line_name="_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62")
    sim = SimulationConfig(power_system_config=psc)

    print(psc.asjson())
    print(sim.asjson())
    pprint(json.loads(sim.asjson()), indent=2)