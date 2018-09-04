import json
import logging
import os
import sys
import time
import random

import stomp

from gridappsd import ApplicationController, GridAPPSD
from gridappsd.topics import (
    REQUEST_REGISTER_APP,
    BASE_APPLICATION_HEARTBEAT,
    REQUEST_APP_START
)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
_log = logging.getLogger(__name__)

if not os.path.exists("/appconfig"):
    _log.error("Invalid /appconfig reference...map the /appconfig to your container")
    sys.exit(1)

config = open("/appconfig").read()

while True:

    try:
        gap = GridAPPSD()
    except stomp.exception.ConnectFailedException:
        _log.debug("Retry in 10 seconds")
        time.sleep(10)
    else:
        # app_config_minimal = {
        #     'id': 'an-app-id',
        #     'execution_path': '/home/osboxes/git/gridappsd-python/testapp.sh'
        # }
        appreg = ApplicationController(config, gridappsd=gap)
        appreg.register_app()
        break

while True:
    time.sleep(2)


