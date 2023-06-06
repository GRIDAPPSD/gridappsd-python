import datetime, time
from enum import Enum
from typing import Optional

from dateutil import parser
import os
try: # python2.7
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse


__GRIDAPPSD_URI__ = os.environ.get("GRIDAPPSD_URI", "localhost:61613")

if not __GRIDAPPSD_URI__.startswith("tcp://"):
    __GRIDAPPSD_URI__ = "tcp://" + __GRIDAPPSD_URI__
__GRIDAPPSD_URI_PARSED__ = urlparse(__GRIDAPPSD_URI__)


def datetime_to_epoche(dt):
    return int(time.mktime(dt.timetuple()) * 1000)


def datestr_to_epoche(dt_str):
    dt = parser.parse(dt_str)
    return datetime_to_epoche(dt)


def epoche_to_datetime(epoche):
    return datetime.datetime.fromtimestamp(epoche)


def utc_timestamp():
    return datetime_to_epoche(datetime.datetime.utcnow())


def validate_gridappsd_uri():
    problems = []

    gridapspd_uri = __GRIDAPPSD_URI__
    if not gridapspd_uri.startswith("tcp://"):
        gridapspd_uri = "tcp://" + gridapspd_uri

    gridapspd_parsed_uri = urlparse(gridapspd_uri)

    if not gridapspd_parsed_uri.port:
        problems.append("Invalid port specified in URI modify environment GRIDAPPSD_URI")

    if not gridapspd_parsed_uri.hostname:
        problems.append("Invalid hostname not specified!")

    return problems


def get_gridappsd_address():
    """
    Returns the address in such a way that the response will be
    able to be passed directly to a socket and/or the stomp library.
    :return: tuple(address, port)
    """
    # New way is to specify the address in environment GRIDAPPSD_ADDRESS and use that
    # for this utility function
    address = os.environ.get("GRIDAPPSD_ADDRESS")
    if address:
        port = os.environ.get("GRIDAPPS_PORT", "61613")
        if address.startswith("tcp://"):
            address = address.replace("tcp://", "")

        return address, port

    return (__GRIDAPPSD_URI_PARSED__.hostname,
            __GRIDAPPSD_URI_PARSED__.port)


def get_gridappsd_application_id():
    """ Retrieve the application_id from the environment.

    In order to use this function an environmental variable `GRIDAPPSD_APPLICATION_ID`
    must have been set.  For docker containers this is done in the
    `gridappsd.app_registration` callback when the application is started.  If the
    environmental variable is not set an AttributeError will be raised.
    """
    app_id = os.environ.get("GRIDAPPSD_APPLICATION_ID")
    if not app_id:
        raise AttributeError("environmental variable for GRIDAPPSD_APPLICATION_ID is not set")
    return app_id


def get_gridappsd_simulation_id() -> Optional[str]:
    """ Retrieve simulation_id from environment.

    This method will return a `None` if the GRIDAPPSD_SIMULATION_ID environmental
    variable is not set.

    return: Optional[str]: simulation_id or None
    """
    simulation_id = os.environ.get("GRIDAPPSD_SIMULATION_ID", None)
    return None if simulation_id is None else str(simulation_id)


class ProcessStatusEnum(Enum):
    STARTING = "STARTING"
    STOPPING = "STOPPING"
    RUNNING = "RUNNING"
    CLOSED = "CLOSED"
    ERROR = "ERROR"
    COMPLETE = "COMPLETE"
    PAUSED = "PAUSED"
    STARTED = "STARTED"
