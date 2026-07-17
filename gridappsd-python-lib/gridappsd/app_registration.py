# import json
import logging
import os
from enum import Enum
from queue import Queue
import time
import subprocess
import threading
import shlex
import sys

from .gridappsd import GridAPPSD
from .topics import REQUEST_REGISTER_APP
from . import utils, json_extension as json

_log = logging.getLogger(__name__)

GRIDAPPSD_APPLICATION_STATUS = "GRIDAPPSD_APPLICATION_STATUS"


class ApplicationStatusEnum(Enum):
    """Values this module writes to the GRIDAPPSD_APPLICATION_STATUS environment variable.

    This is a distinct enum from gridappsd.utils.ProcessStatusEnum: this module's
    STOPPED value has no equivalent in ProcessStatusEnum (which has CLOSED
    instead), so reusing that enum here would either drop STOPPED or introduce
    a mismatch between the value written and the value a reader expects.
    """

    STARTING = "STARTING"
    STOPPING = "STOPPING"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


def _set_application_status(status: ApplicationStatusEnum) -> None:
    """Write status to the GRIDAPPSD_APPLICATION_STATUS environment variable."""
    os.environ[GRIDAPPSD_APPLICATION_STATUS] = status.value


# determine OS type
posix = False
if os.name == "posix":
    posix = True


class Job(threading.Thread):
    def __init__(self, args, out=sys.stdout, err=sys.stderr):
        threading.Thread.__init__(self)
        _log.debug("Creating job")
        self.running = False
        self._args = args
        self._out = out
        self._err = err

    def shutdown(self):
        self.running = False

    def run(self):
        try:
            self.running = True
            _set_application_status(ApplicationStatusEnum.RUNNING)

            p = subprocess.Popen(args=self._args, shell=False, stdout=self._out, stderr=self._err)

            # Loop while process is executing
            while p.poll() is None and self.running:
                _set_application_status(ApplicationStatusEnum.RUNNING)
                time.sleep(1)

        except Exception as e:
            _set_application_status(ApplicationStatusEnum.ERROR)
            _log.error(repr(e))
        else:
            _set_application_status(ApplicationStatusEnum.STOPPED)


class ApplicationController(object):
    def __init__(self, config, gridappsd=None, heatbeat_period=10):
        if not isinstance(config, dict):
            raise ValueError("Config should be dictionary")
        if not isinstance(gridappsd, GridAPPSD):
            raise ValueError("Invalid gridappsd instance passed.")

        _set_application_status(ApplicationStatusEnum.STOPPED)
        self._configDict = config.copy()
        self._validate_config()
        self._gapd = gridappsd
        self._shutting_down = False
        self._heartbeat_thread = None
        self._heartbeat_period = heatbeat_period
        self._heartbeat_should_stop = False
        self._application_id = None
        self._heartbeat_topic = None
        self._start_control_topic = None
        self._stop_control_topic = None
        self._status_control_topic = None
        self._thread = None
        self._jobs = []
        self._process_start_time = None
        self._process_end_time = None
        self._process_is_running = False
        self._process_has_started = False
        self._end_callback = None
        self._print_queue = Queue()
        self._heartbeat_thread = None
        _set_application_status(ApplicationStatusEnum.STOPPED)

        if "type" not in self._configDict or self._configDict["type"] != "REMOTE":
            _log.warning(
                'Setting type to REMOTE you can remove this error by putting "type": "REMOTE" in the app config file.'
            )
            self._configDict["type"] = "REMOTE"

    def _validate_config(self):
        required = ["id", "execution_path"]
        missing = [x for x in required if x not in self._configDict]

        if missing:
            raise ValueError("Missing {} in config object.".format(missing))

    @property
    def application_id(self):
        return self._application_id

    @property
    def heartbeat_valid(self):
        return self._heartbeat_thread is not None

    def register_app(self, end_callback):
        print("Sending {}\n\tto {}".format(self._configDict, REQUEST_REGISTER_APP))
        self._gapd.get_logger().debug("Started App Registration")

        response = self._gapd.get_response(REQUEST_REGISTER_APP, self._configDict, 60)
        if "message" in response:
            _log.error("An error regisering the application occured")
            _log.error(response.get("message"))
            raise ValueError(response.get("message"))
        self._application_id = response.get("applicationId")
        self._heartbeat_topic = response.get("heartbeatTopic")
        self._heartbeat_period = response.get("heartbeatPeriod", 10)
        self._start_control_topic = response.get("startControlTopic")
        self._stop_control_topic = response.get("stopControlTopic")

        os.environ["GRIDAPPSD_APPLICATION_ID"] = self._application_id
        _set_application_status(ApplicationStatusEnum.STOPPED)

        self._gapd.subscribe(self._stop_control_topic, self.__handle_stop)
        self._gapd.subscribe(self._start_control_topic, self.__handle_start)
        self._end_callback = end_callback

        # TODO assuming good response start the heartbeat
        self._heartbeat_thread = threading.Thread(target=self.__start_heartbeat, args=[self.__heartbeat_error])
        self._heartbeat_thread.daemon = True
        self._heartbeat_thread.start()
        self._gapd.get_logger().debug(
            "Heartbeat registereed for application {}".format(utils.get_gridappsd_application_id())
        )

    def __heartbeat_error(self):
        self._heartbeat_thread = None

    def __start_heartbeat(self, error_callback):
        starttime = time.time()

        try:
            while True:
                self._print_queue.put("Sending heartbeat for {}".format(self._application_id))
                # print("Seanding heartbeat {} {}".format(self._heartbeat_topic, self._application_id))
                # print("Heartbeat period: {}".format(self._heartbeat_period))
                self._gapd.send(self._heartbeat_topic, self._application_id)
                time.sleep(self._heartbeat_period - ((time.time() - starttime) % self._heartbeat_period))
        except:
            error_callback()

    def __print_from_queue(self):
        while True:
            buff = self._print_queue.get(block=True)
            print(buff)

    def __handle_start(self, headers, message):
        _log.debug("Handling start")
        if isinstance(message, str):
            obj = json.loads(message)
        else:
            obj = message
        _set_application_status(ApplicationStatusEnum.STARTING)
        self._gapd.get_logger().debug("Handling Start: {}\ndict:\n{}".format(headers, obj))

        if "command" not in obj:
            # Send log to gridappsd
            _log.error("Invalid message sent on start app.")
        else:
            _log.debug("CWD IS: {}".format(os.getcwd()))
            args = shlex.split(obj["command"])
            job = Job(args)
            job.daemon = True
            job.start()
            self._gapd.get_logger().debug("Job Started: {}".format(job.running))

    def __handle_stop(self, headers, message):
        print("Handling Stop: {} {}".format(headers, message))
        _set_application_status(ApplicationStatusEnum.STOPPING)
        if self._thread:
            self._thread.join()
        if self._end_callback is not None:
            self._end_callback()
        _set_application_status(ApplicationStatusEnum.STOPPED)

    def shutdown(self):
        self._shutting_down = True
