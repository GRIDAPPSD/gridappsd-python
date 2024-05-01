import logging
import os
import socket
import time

import stomp

from gridappsd import GridAPPSD

logging.basicConfig(level=logging.DEBUG)

_log = logging.getLogger(__name__)

os.environ["GRIDAPPSD_USER"] = "system"
os.environ["GRIDAPPSD_PASSWORD"] = "manager"
os.environ["GRIDAPPSD_ADDRESS"] = "gridappsd"
os.environ["GRIDAPPSD_PORT"] = "61613"

gapps = None

while gapps is None:
    try:
        gapps = GridAPPSD()
    except (ConnectionRefusedError, stomp.exception.ConnectFailedException, socket.gaierror,
            OSError):
        _log.debug("Not Connected")
        time.sleep(5)
    else:
        _log.debug("Connected!")

_log.debug("Complete!")
gapps.disconnect()
