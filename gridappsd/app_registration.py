import json
import logging
import time
import threading
import subprocess

from . gridappsd import GridAPPSD
from . topics import REQUEST_REGISTER_APP

_log = logging.getLogger(__name__)


class ApplicationController(object):

    def __init__(self, config, gridappsd=None, heatbeat_period=10):
        if not isinstance(config, dict):
            raise ValueError("Config should be dictionary")
        if not isinstance(gridappsd, GridAPPSD):
            raise ValueError("Invalid gridappsd instance passed.")

        self._configDict = config.copy()
        self._validate_config()
        self._gapd = gridappsd
        self._shutting_down = False
        self._heartbeat_thread = None
        self._heartbeat_period = heatbeat_period
        self._application_id = None
        self._heartbeat_topic = None
        self._start_control_topic = None
        self._stop_control_topic = None
        self._status_control_topic = None
        self._process = None

        if "type" not in self._configDict or self._configDict['type'] != 'REMOTE':
            _log.warn('Setting type to REMOTE you can remove this error by putting '
                      '"type": "REMOTE" in the app config file.')
            self._configDict['type'] = 'REMOTE'

    def _validate_config(self):
        required = ['id', 'execution_path']
        missing = [x for x in required if x not in self._configDict]

        if missing:
            raise ValueError("Missing {} in config object.".format(missing))

    @property
    def application_id(self):
        return self._application_id

    def register_app(self):
        print("Sending {}\n\tto {}".format(self._configDict,
                                           REQUEST_REGISTER_APP))
        response = self._gapd.get_response(REQUEST_REGISTER_APP,
                                           self._configDict,
                                           60)

        self._application_id = response.get('applicationId')
        self._heartbeat_topic = response.get('heartbeatTopic')
        self._heartbeat_period = response.get('heartbeatPeriod', 10)
        self._start_control_topic = response.get('startControlTopic')
        self._stop_control_topic = response.get('stopControlTopic')

        self._gapd.subscribe(self._stop_control_topic, self.__handle_stop)
        self._gapd.subscribe(self._start_control_topic, self.__handle_start)

        # TODO assuming good response start the heartbeat
        t = threading.Thread(target=self.__start_heartbeat)
        t.daemon = True
        t.start()

    def __start_heartbeat(self):
        starttime = time.time()
        while True:
            print("Sending")
            self._gapd.send(self._heartbeat_topic, 'tick')
            time.sleep(self._heartbeat_period - ((time.time() - starttime) % self._heartbeat_period))

    def __handle_start(self, headers, message):
        obj = json.loads(message)
        if 'command' not in obj:
            # Send log to gridappsd
            _log.error("Invalid message sent on start app.")
        else:
            _log.debug("Attempting to start: {}".format(obj['command']))
            args = obj['command'].split(' ')
            args.insert(0, '/e/git/gridappsd-python/venv/Scripts/python')
            subprocess.call(args=args)
        print("Handling Start: {} {}".format(headers, message))


    def __handle_stop(self, headers, message):
        print("Handling Stop: {} {}".format(headers, message))

    def shutdown(self):
        self._shutting_down = True