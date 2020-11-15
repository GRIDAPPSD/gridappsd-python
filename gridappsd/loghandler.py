import json
import logging
import os

from . import topics as t
from . import utils

VALID_LOG_LEVELS = [logging.DEBUG, logging.INFO, logging.ERROR, logging.WARNING, logging.FATAL, logging.WARN]


class Logger:
    """
    The `Logger` class handles logging to the main gridappsd server.
    """
    def __init__(self, gaps, level=logging.INFO):
        self._gaps = gaps
        self._level = level

    def setLevel(self, level):
        self._level = level

    def debug(self, message):
        self.log(message)

    def info(self, message):
        self.log(message, logging.INFO)

    def error(self, message):
        self.log(message, logging.ERROR)

    def warning(self, message):
        self.log(message, logging.WARNING)

    def fatal(self, message):
        self.log(message, logging.FATAL)

    def log(self, message, level=logging.DEBUG):
        """
        Log message to the gridappsd logging api.

        :raises: AttributeError
            if the environment doesn't have GRIDAPPSD_APPLICATION_ID or GRIDAPPSD_SERVICE_ID or
            GRIDAPPSD_PROCESS_ID in the environment
        """
        process_identifier = self._gaps.get_application_id()

        if not level in VALID_LOG_LEVELS:
            raise AttributeError(f"Log level must be one of {[logging.getLevelName(x) for x in VALID_LOG_LEVELS]}")

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
            "logLevel": logging.getLevelName(level),
            "storeToDb": True
        }

        self._gaps.send(topic, status_message)
