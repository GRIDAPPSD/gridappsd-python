import inspect
import json
import logging
from logging import DEBUG, INFO, WARNING, FATAL, ERROR
import sys

import yaml

from . import GridAPPSD
import fncs

_log = logging.getLogger(inspect.getmodulename(__file__))

DEFAULT_FNCS_LOCATION = 'tcp://localhost:5570'
DEFAULT_INPUT_TOPIC = '/topic/goss.gridappsd.simulation.input'
DEFAULT_OUTPUT_TOPIC = '/topic/goss.gridappsd.simulation.output'
BASE_SIMULATION_STATUS_TOPIC = "/topic/goss.gridappsd.process.log.simulation"


class GridAPPSDListener(object):
    def __init__(self, fncs_bridge, gridappsd):
        if not fncs_bridge:
            raise AttributeError("fncs_bridge must be set!")
        self._bridge = fncs_bridge
        self._gridappsd = gridappsd

    def on_message(self, headers, msg):
        message = {}
        try:
            message_str = 'received message ' + str(msg)
            if fncs.is_initialized():
                self._gridappsd.send_simulation_status('RUNNING', message_str, DEBUG)
            else:
                self._gridappsd.send_simulation_status('STARTED', message_str, DEBUG)

            json_msg = yaml.safe_load(str(msg))
            if json_msg['command'] == 'isInitialized':
                message_str = 'isInitialized check: ' + str(is_initialized)
                if fncs.is_initialized():
                    self._gridappsd.send_simulation_status('RUNNING', message_str, DEBUG)
                else:
                    self._gridappsd.send_simulation_status('STARTED', message_str, DEBUG)
                message['command'] = 'isInitialized'
                message['response'] = str(is_initialized)
                if self.simulation_id is not None:
                    message['output'] = self._bridge.get_messages_from_fncs()
                message_str = 'Added isInitialized output, sending message {}'.format(message)

                if fncs.is_initialized():
                    self._gridappsd.send_simulation_status('RUNNING', message_str, DEBUG)
                else:
                    self._gridappsd.send_simulation_status('RUNNING', message_str, DEBUG)
                self._gridappsd.send(topic=self._bridge.simulation_output_topic,
                                     message=json.dumps(message))
            elif json_msg['command'] == 'update':
                message['command'] = 'update'
                # does not return
                self._bridge.publish_to_fncs(json.dumps(json_msg['message']))
            elif json_msg['command'] == 'nextTimeStep':
                message_str = 'is next timestep'
                self._gridappsd.send_simulation_status('RUNNING', message_str, DEBUG)
                message['command'] = 'nextTimeStep'
                current_time = json_msg['currentTime']
                message_str = 'incrementing to ' + str(current_time)
                self._gridappsd.send_simulation_status('RUNNING', message_str, DEBUG)
                # current_time is incrementing integer 0 ,1, 2.... representing seconds
                self._bridge.timestep_complete(current_time)
                message_str = 'done with timestep ' + str(current_time)
                self._gridappsd.send_simulation_status('RUNNING', message_str, DEBUG)
                message_str = 'simulation id ' + str(self._bridge.simulation_id)
                self._gridappsd.send_simulation_status('RUNNING', message_str, DEBUG)
                message['output'] = self._bridge.get_messages_from_fncs()
                response_msg = json.dumps(message)
                message_str = 'sending fncs output message ' + str(response_msg)
                self._gridappsd.send_simulation_status('RUNNING', message_str, DEBUG)
                self._gridappsd.send(topic=self._bridge.simulation_output_topic,
                                     message=json.dumps(message))
            elif json_msg['command'] == 'stop':
                message_str = 'Stopping the simulation'
                self._gridappsd.send_simulation_status('STOPPED', message_str)
                fncs.die()
                sys.exit()

        except Exception as e:
            message_str = 'Error in command ' + str(e)
            self._gridappsd.send_simulation_status('ERROR', message_str, ERROR)
            if fncs.is_initialized():
                fncs.die()

    def on_error(self, headers, message):
        message_str = 'Error in {} {}'.format('GridAPPSDListener', message)
        self._gridappsd.send_simulation_status('STOPPED', message_str)
        if fncs.is_initialized():
            fncs.die()

    def on_disconnected(self):
        if fncs.is_initialized():
            fncs.die()


class FncsBridge(object):

    def __init__(self, simulation_id,
                 fncs_broker_location='tcp://localhost:5570',
                 base_input_topic='/topic/goss.gridappsd.simulation.input',
                 base_output_topic="/topic/goss.gridappsd.simulation.output",
                 connect_now=True):

        if not base_input_topic.endswith('.'):
            base_input_topic += '.'

        if not base_output_topic.endswith('.'):
            base_output_topic += '.'

        self.fncs_broker_location = fncs_broker_location
        self.simulation_input_topic = base_input_topic + str(simulation_id)
        self.simulation_output_topic = base_output_topic + str(simulation_id)
        self.simulation_id = str(simulation_id)

        self._gridappsd = None
        self._gridappsd_listener = None

        if connect_now:
            self.start_bridge()

    def timestep_complete(self, current_time):
        """tell the fncs_broker to move to the next time step.

            Function arguments:
                current_time -- Type: integer. Description: the current time in seconds.
                    It must not be none.
            Function returns:
                None.
            Function exceptions:
                RuntimeError()
                ValueError()
            """
        try:
            message_str = 'In done with timestep ' + str(current_time)
            self._gridappsd.send_simulation_status('RUNNING', message_str, DEBUG)
            if current_time or type(current_time) != int:
                raise ValueError(
                    'current_time must be an integer.\n'
                    + 'current_time = {0}'.format(current_time))
            time_request = current_time + 1
            message_str = 'calling time_request ' + str(time_request)
            self._gridappsd.send_simulation_status('RUNNING', message_str, DEBUG)
            time_approved = fncs.time_request(time_request)
            message_str = 'time approved ' + str(time_approved)
            self._gridappsd.send_simulation_status('RUNNING', message_str, DEBUG)
            if time_approved != time_request:
                raise RuntimeError(
                    'The time approved from fncs_broker is not the time requested.\n'
                    + 'time_request = {0}.\ntime_approved = {1}'.format(time_request,
                                                                        time_approved))
        except Exception as e:
            message_str = 'Error in fncs timestep ' + str(e)
            self._gridappsd.send_simulation_status('ERROR', message_str, ERROR)

    def publish_to_fncs(self, goss_message):
        """publish a message received from the GOSS bus to the FNCS bus.

        Function arguments:
            simulation_id -- Type: string. Description: The simulation id.
                It must not be an empty string. Default: None.
            goss_message -- Type: string. Description: The message from the GOSS bus
                as a json string. It must not be an empty string. Default: None.
        Function returns:
            None.
        Function exceptions:
            RuntimeError()
            ValueError()
        """
        message_str = 'publish to fncs bus {} {}'.format(self.simulation_id, goss_message)
        self._gridappsd.send_simulation_status('RUNNING', message_str, DEBUG)

        if not self.simulation_id or type(self.simulation_id) != str:
            raise ValueError(
                'simulation_id must be a nonempty string.\n'
                + 'simulation_id = {0}'.format(self.simulation_id))
        if not goss_message or type(goss_message) != str:
            raise ValueError(
                'goss_message must be a nonempty string.\n'
                + 'goss_message = {0}'.format(goss_message))
        if not fncs.is_initialized():
            raise RuntimeError(
                'Cannot publish message as there is no connection'
                + ' to the FNCS message bus.')
        try:
            test_goss_message_format = yaml.safe_load(goss_message)
            if type(test_goss_message_format) != dict:
                raise ValueError(
                    'goss_message is not a json formatted string.'
                    + '\ngoss_message = {0}'.format(goss_message))
        except ValueError as ve:
            raise ValueError(ve)
        except:
            raise RuntimeError(
                'Unexpected error occured while executing yaml.safe_load(goss_message'
                + '{0}'.format(sys.exc_info()[0]))
        fncs_input_topic = '{0}/fncs_input'.format(self.simulation_id)
        message_str = 'fncs input topic ' + fncs_input_topic
        self._gridappsd.send_simulation_status('RUNNING', message_str, DEBUG)
        fncs.publish_anon(fncs_input_topic, goss_message)

    def get_messages_from_fncs(self):
        """publish a message received from the GOSS bus to the FNCS bus.

            Function arguments:
                simulation_id -- Type: string. Description: The simulation id.
                    It must not be an empty string. Default: None.
            Function returns:
                fncs_output -- Type: string. Description: The json structured output
                    from the simulation. If no output was sent from the simulation then
                    it returns None.
            Function exceptions:
                ValueError()
            """
        try:
            fncs_output = None
            if not self.simulation_id or type(self.simulation_id) != str:
                raise ValueError(
                    'self.simulation_id must be a nonempty string.\n'
                    + 'simulation_id = {0}'.format(self.simulation_id))
            message_str = 'about to get fncs events'
            self._gridappsd.send_simulation_status('RUNNING', message_str, DEBUG)
            message_events = fncs.get_events()
            message_str = 'fncs events ' + str(message_events)
            self._gridappsd.send_simulation_status('RUNNING', message_str, DEBUG)
            if self.simulation_id in message_events:
                fncs_output = fncs.get_value(self.simulation_id)
            message_str = 'fncs_output ' + str(fncs_output)
            self._gridappsd.send_simulation_status('RUNNING', message_str, DEBUG)
            return fncs_output
        except Exception as e:
            message_str = 'Error on get FncsBusMessages for ' + str(self.simulation_id) + ' ' + str(e)
            self._gridappsd.send_simulation_status('ERROR', message_str, ERROR)

    def start_bridge(self):
        """Register with the fncs_broker and return.

            Function arguments:
                broker_location -- Type: string. Description: The ip location and port
                    for the fncs_broker. It must not be an empty string.
                    Default: 'tcp://localhost:5570'.
            Function returns:
                None.
            Function exceptions:
                RuntimeError()
                ValueError()
            """
        global is_initialized

        # First connect with goos via the GridAPPSD interface
        self._gridappsd = GridAPPSD(self.simulation_id, id=2,
                                    base_simulation_status_topic=BASE_SIMULATION_STATUS_TOPIC)
        self._gridappsd_listener = GridAPPSDListener(self, self._gridappsd)

        self._gridappsd.subscribe(self.simulation_input_topic,
                                  callback=self._gridappsd_listener)
        self._gridappsd.send_simulation_status("STARTING",
                                               "Starting Bridge for simulation id: {}".format(self.simulation_id))

        configuration_zpl = ''
        try:

            message_str = 'Registering with FNCS broker ' + str(self.simulation_id) + ' and broker ' + self.fncs_broker_location
            self._gridappsd.send_simulation_status("STARTED", message_str)

            message_str = 'connected to goss {}'.format(self._gridappsd.connected)
            self._gridappsd.send_simulation_status("STARTED", message_str)
            if not self.simulation_id or type(self.simulation_id) != str:
                raise ValueError(
                    'simulation_id must be a nonempty string.\n'
                    + 'simulation_id = {0}'.format(self.simulation_id))

            if not self.fncs_broker_location or type(self.fncs_broker_location) != str:
                raise ValueError(
                    'broker_location must be a nonempty string.\n'
                    + 'broker_location = {0}'.format(self.fncs_broker_location))
            fncs_configuration = {
                'name': 'FNCS_GOSS_Bridge_' + self.simulation_id,
                'time_delta': '1s',
                'broker': self.fncs_broker_location,
                'values': {
                    self.simulation_id: {
                        'topic': self.simulation_id + '/fncs_output',
                        'default': '{}',
                        'type': 'JSON',
                        'list': 'false'
                    }
                }
            }

            configuration_zpl = ('name = {0}\n'.format(fncs_configuration['name'])
                                 + 'time_delta = {0}\n'.format(fncs_configuration['time_delta'])
                                 + 'broker = {0}\nvalues'.format(fncs_configuration['broker']))
            for x in fncs_configuration['values'].keys():
                configuration_zpl += '\n    {0}'.format(x)
                configuration_zpl += '\n        topic = {0}'.format(
                    fncs_configuration['values'][x]['topic'])
                configuration_zpl += '\n        default = {0}'.format(
                    fncs_configuration['values'][x]['default'])
                configuration_zpl += '\n        type = {0}'.format(
                    fncs_configuration['values'][x]['type'])
                configuration_zpl += '\n        list = {0}'.format(
                    fncs_configuration['values'][x]['list'])
            fncs.initialize(configuration_zpl)

            is_initialized = fncs.is_initialized()
            if is_initialized:
                message_str = 'Registered with fncs ' + str(is_initialized)
                self._gridappsd.send_simulation_status("RUNNING", message_str)

        except Exception as e:
            message_str = 'Error while registering with fncs broker ' + str(e)
            self._gridappsd.send_simulation_status('ERROR', message_str, 'ERROR')
            if fncs.is_initialized():
                fncs.die()

        if not fncs.is_initialized():
            message_str = 'fncs.initialize(configuration_zpl) failed!\n' + 'configuration_zpl = {0}'.format(
                configuration_zpl)
            self._gridappsd.send_simulation_status('ERROR', message_str, 'ERROR')
            if fncs.is_initialized():
                fncs.die()
            raise RuntimeError(
                'fncs.initialize(configuration_zpl) failed!\n'
                + 'configuration_zpl = {0}'.format(configuration_zpl))


