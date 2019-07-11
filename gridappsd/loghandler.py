import json
import logging
import os

from . import topics as t
from . import utils


class Logger:
    """
    The `Logger` class handles logging to the main gridappsd server.
    """
    def __init__(self, gaps):
        self._gaps = gaps

    def debug(self, message):
        self.log(message)

    def info(self, message):
        self.log(message, logging.INFO)

    def error(self, message):
        self.log(message, logging.ERROR)

    def warning(self, message):
        self.log(message, logging.WARNING)

    def log(self, message, level=logging.DEBUG):
        status = os.environ.get("GRIDAPPSD_APPLICATION_STATUS")
        if not status:
            raise AttributeError("Invalid GRIDAPPSD_APPLICATION_STATUS environmental variable.")
        sim_id = utils.get_gridappsd_simulation_id()
        if sim_id is not None:
            topic = t.simulation_log_topic(sim_id)
        else:
            topic = t.platform_log_topic()

        status_message = {
            "source": utils.get_gridappsd_application_id(),
            "processId": "{}-{}".format(utils.get_gridappsd_application_id(), sim_id),
            "processStatus": str(status),
            "logMessage": str(message),
            "logLevel": logging.getLevelName(level),
            "storeToDb": True
        }

        self._gaps.send(topic, status_message)
