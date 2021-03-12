from logging import FATAL, ERROR, WARN, WARNING, INFO, DEBUG, NOTSET
import os

from . import topics as t

_nameToLevel = {
    'FATAL': FATAL,
    'ERROR': ERROR,
    'WARN': WARN,
    'WARNING': WARN,
    'INFO': INFO,
    'DEBUG': DEBUG,
    'NOTSET': NOTSET,
}

_levelToName = {
    FATAL: 'FATAL',
    ERROR: 'ERROR',
    WARNING: 'WARN',
    WARN: 'WARN',
    INFO: 'INFO',
    DEBUG: 'DEBUG',
    NOTSET: 'NOTSET',
}

VALID_LOG_LEVELS = set(_nameToLevel.values())


def getNameToLevel(level: str) -> int:
    data = level.upper()
    return _nameToLevel.get(data, NOTSET)


class Logger:
    """
    The `Logger` class handles logging to the main gridappsd server.
    """
    def __init__(self, gaps, level=INFO):
        self._gaps = gaps
        self._level = level

    def setLevel(self, level):
        self._level = level

    def debug(self, message):
        self.log(message)

    def info(self, message):
        self.log(message, INFO)

    def error(self, message):
        self.log(message, ERROR)

    def warning(self, message):
        self.log(message, WARNING)

    def fatal(self, message):
        self.log(message, FATAL)

    def log(self, message, level=DEBUG):
        """
        Log message to the gridappsd logging api.

        :raises: AttributeError
            if the environment doesn't have GRIDAPPSD_APPLICATION_ID or GRIDAPPSD_SERVICE_ID or
            GRIDAPPSD_PROCESS_ID in the environment
        """
        process_identifier = self._gaps.get_application_id()

        if not level in VALID_LOG_LEVELS:
            raise AttributeError(f"Log level must be one of {[x for x in _levelToName.values()]}")

        if not process_identifier:
            raise AttributeError(f"Must have GRIDAPPSD_APPLICATION_ID or GRIDAPPSD_SERVICE_ID or GRIDAPPSD_PROCESS_ID "
                                 "set in os environments.")
        status = self._gaps.get_application_status()
        sim_id = self._gaps.get_simulation_id()

        if sim_id is not None:
            topic = t.simulation_log_topic(sim_id)
        else:
            topic = t.platform_log_topic()

        status_message = {
            "source": process_identifier,
            "processId": f"{sim_id}",
            "processStatus": str(status),
            "logMessage": str(message),
            "logLevel": _levelToName[level],
            "storeToDb": True
        }
        
        gridappsd_log_level = os.getenv('GRIDAPPSD_LOG_LEVEL')
        if gridappsd_log_level == None:
            gridappsd_log_level = level
        else:
            gridappsd_log_level = _nameToLevel[gridappsd_log_level]
            
        if level >= gridappsd_log_level:
            self._gaps.send(topic, status_message)

