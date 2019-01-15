import json
import logging
import os
import sys
import time
import stomp
from gridappsd import ApplicationController, GridAPPSD, utils


logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format="%(asctime)s - %(name)s;%(levelname)s|%(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
logging.getLogger('stomp.py').setLevel(logging.ERROR)
_log = logging.getLogger(__name__)

problems = utils.validate_gridappsd_uri()

if problems:
    for p in problems:
        _log.error(p)
    sys.exit(1)

gridapspd_address = utils.get_gridappsd_address()
gridapspd_user = utils.get_gridappsd_user()
gridappsd_pass = utils.get_gridappsd_pass()

if not os.path.isfile("/appconfig"):
    _log.error("Invalid /appconfig reference...map the /appconfig to your container")
    sys.exit(1)

config = json.loads(open("/appconfig").read())
appreg = None
gap = None
while True:

    try:
        if gap is None:
            gap = GridAPPSD(username=gridapspd_user, password=gridappsd_pass,
                            address=utils.get_gridappsd_address())

    except ConnectionRefusedError:  # Python 3 specific error code
        _log.debug("Retry in 10 seconds")
        gap = appreg = None
        time.sleep(10)
    except (stomp.exception.ConnectFailedException, OSError):
        _log.debug("Connect failed Retry in 10 seconds")
        gap = appreg = None
        time.sleep(10)
    else:
        if appreg is None:
            def end_app():
                sys.exit(0)

            # app_config_minimal = {
            #     'id': 'an-app-id',
            #     'execution_path': '/home/osboxes/git/gridappsd-python/testapp.sh'
            # }
            try:
                appreg = ApplicationController(config, gridappsd=gap)
                appreg.register_app(end_app)
                _log.info('Application {} registered.'.format(config['id']))
            except:
                _log.exception("An unhandled exception occured retrying app")
                appreg = None
                gap = None
        else:
            if not appreg.heartbeat_valid:
                appreg = None
                gap = None

        time.sleep(2)


