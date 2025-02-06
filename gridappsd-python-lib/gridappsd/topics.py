# -------------------------------------------------------------------------------
# Copyright (c) 2018, Battelle Memorial Institute All rights reserved.
# Battelle Memorial Institute (hereinafter Battelle) hereby grants permission to any person or entity
# lawfully obtaining a copy of this software and associated documentation files (hereinafter the
# Software) to redistribute and use the Software in source and binary forms, with or without modification.
# Such person or entity may use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and may permit others to do so, subject to the following conditions:
# Redistributions of source code must retain the above copyright notice, this list of conditions and the
# following disclaimers.
# Redistributions in binary form must reproduce the above copyright notice, this list of conditions and
# the following disclaimer in the documentation and/or other materials provided with the distribution.
# Other than as used herein, neither the name Battelle Memorial Institute or Battelle may be used in any
# form whatsoever without the express written consent of Battelle.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# BATTELLE OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
# General disclaimer for use with OSS licenses
#
# This material was prepared as an account of work sponsored by an agency of the United States Government.
# Neither the United States Government nor the United States Department of Energy, nor Battelle, nor any
# of their employees, nor any jurisdiction or organization that has cooperated in the development of these
# materials, makes any warranty, express or implied, or assumes any legal liability or responsibility for
# the accuracy, completeness, or usefulness or any information, apparatus, product, software, or process
# disclosed, or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer,
# or otherwise does not necessarily constitute or imply its endorsement, recommendation, or favoring by the United
# States Government or any agency thereof, or Battelle Memorial Institute. The views and opinions of authors expressed
# herein do not necessarily state or reflect those of the United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY operated by BATTELLE for the
# UNITED STATES DEPARTMENT OF ENERGY under Contract DE-AC05-76RL01830
# -------------------------------------------------------------------------------
DEFAULT_FNCS_LOCATION = 'tcp://localhost:5570'

BASE_TOPIC = '/topic/goss.gridappsd'
FNCS_BASE_INPUT_TOPIC = '/topic/goss.gridappsd.simulation.input'
FNCS_BASE_OUTPUT_TOPIC = '/topic/goss.gridappsd.simulation.output'
BASE_SIMULATION_TOPIC = '/topic/goss.gridappsd.simulation'
BASE_SIMULATION_LOG_TOPIC = "/topic/goss.gridappsd.simulation.log"
BASE_FIELD_TOPIC = '/topic/goss.gridappsd.field'

BASE_FIELD_QUEUE = 'goss.gridappsd.field'
REGISTER_AGENT_QUEUE = 'goss.gridappsd.field.register.agent'

BLAZEGRAPH = "/queue/goss.gridappsd.process.request.data.powergridmodel"
# https://gridappsd.readthedocs.io/en/latest/using_gridappsd/index.html#querying-logs
LOGS = "/queue/goss.gridappsd.process.request.data.log"
# https://gridappsd.readthedocs.io/en/latest/using_gridappsd/index.html#timeseries-api
TIMESERIES = "/queue/goss.gridappsd.process.request.data.timeseries"

CONFIG = "/queue/goss.gridappsd.process.request.config"
PLATFORM_STATUS = "/queue/goss.gridappsd.process.request.status.platform"

BASE_TOPIC_PREFIX = "goss.gridappsd"
PROCESS_PREFIX = ".".join((BASE_TOPIC_PREFIX, "process"))
REQUEST_PLATFORM_STATUS = ".".join([PROCESS_PREFIX, "request.status.platform"])

REQUEST_DATA = ".".join((PROCESS_PREFIX, "request.data"))
REQUEST_SIMULATION_STATUS = ".".join((PROCESS_PREFIX, "request.status.simulation"))
REQUEST_SIMULATION = ".".join((PROCESS_PREFIX, "request.simulation"))

REQUEST_POWERGRID_DATA = ".".join((REQUEST_DATA, "powergridmodel"))
REQUEST_TIMESERIES_DATA = ".".join((REQUEST_DATA, "timeseries"))

REQUEST_REGISTER_APP = ".".join((PROCESS_PREFIX, "request.app.remote.register"))
REQUEST_APP_START = ".".join((PROCESS_PREFIX, "request.app.start"))
BASE_APPLICATION_HEARTBEAT = ".".join((BASE_TOPIC_PREFIX, "heartbeat"))


def platform_log_topic():
    """ Utility method for getting the platform.log base topic
    """
    return "/topic/{}.{}".format(BASE_TOPIC_PREFIX, "platform.log")


def service_input_topic(service_id: str, simulation_id: int | str | None = None):
    """ Utility method for getting the input topic for a specific service.

    The service id should be the registered service with the platform.  One
    can get the list of registered services by using the `GridAPPSD.get_platform_status()`
    method with services=True.

    Examples of service_id are as follows:
        - dnp3

    :param service_id:
    :param simulation_id:
    :return:
    """
    assert service_id, "service_id cannot be empty"

    if simulation_id:
        return f"{BASE_SIMULATION_TOPIC}.{service_id}.{simulation_id}.input"

    return f"{BASE_SIMULATION_TOPIC}.{service_id}.input"


def service_output_topic(service_id: str, simulation_id: int | str | None = None):
    """ Utility method for getting the output topic for a specific service.

    The service id should be the registered service with the platform.  One
    can get the list of registered services by using the `GridAPPSD.get_platform_status()`
    method with services=True.

    Examples of service_id are as follows:
        - dnp3

    :param service_id:
    :param simulation_id:
    :return:str: Topic to subscribe to for service specific output.
    """
    assert service_id, "Service id cannot be empty"

    if simulation_id:
        return f"{BASE_SIMULATION_TOPIC}.{service_id}.{simulation_id}.output"

    return f"{BASE_SIMULATION_TOPIC}.{service_id}.output"


def application_input_topic(application_id: str, simulation_id: int | str | None = None):
    """ Utility method for getting the input topic for a specific application.

    The application_id should be the registered service with the platform.  One
    can get the list of registered application by using the `GridAPPSD.get_platform_status()`
    method with applications=True.

    :param application_id:
    :param simulation_id:
    :return:str: Topic to publish to for a specific application.
    """
    assert application_id, "application_id cannot be empty"

    if simulation_id:
        return f"{BASE_SIMULATION_TOPIC}.{application_id}.{simulation_id}.input"

    return f"{BASE_TOPIC}.{application_id}.input"


def application_output_topic(application_id: str, simulation_id: int | str | None = None):
    """ Utility method for getting the output topic for a specific application.

    The application_id should be the registered service with the platform.  One
    can get the list of registered application by using the `GridAPPSD.get_platform_status()`
    method with applications=True.

    :param application_id:
    :param simulation_id:
    :return: str: Topic to subscribe to for application specific output.
    """
    assert application_id, "application_id cannot be empty"

    if simulation_id:
        return f"{BASE_SIMULATION_TOPIC}.{application_id}.{simulation_id}.output"

    return f"{BASE_TOPIC}.{application_id}.output"


def simulation_output_topic(simulation_id):
    """ Gets the topic for subscribing to output from the simulation.

    :param simulation_id:
    :return: str: Topic to subscribe to data from teh simulation.
    """
    return "{}.{}.{}".format(BASE_SIMULATION_TOPIC, 'output', simulation_id)


def simulation_input_topic(simulation_id):
    """ Gets the topic to write data to for the simulation

    :param simulation_id:
    :return: str: Topic to write data for the simulation.
    """
    return "{}.{}.{}".format(BASE_SIMULATION_TOPIC, 'input', simulation_id)


def simulation_log_topic(simulation_id):
    """https://gridappsd.readthedocs.io/en/latest/using_gridappsd/index.html#subscribing-to-logs
    """
    return "{}.{}".format(BASE_SIMULATION_LOG_TOPIC, simulation_id)


def field_message_bus_topic(message_bus_id: str, app_id: str = None, agent_id: str = None):
    """ Utility method for getting the publish/subscribe topic for a specific message bus.

    :param message_bus_id:
    :param app_id:
    :param agent_id:
    :return:
    """
    assert message_bus_id, "message_bus_id cannot be empty"

    return f"{BASE_FIELD_TOPIC}.{message_bus_id}"


def field_message_bus_app_topic(message_bus_id, app_id=None):
    """ Utility method for getting the publish/subscribe topic for a specific message bus.

    :param message_bus_id:
    :param app_id:
    :return:
    """
    assert message_bus_id, "message_bus_id cannot be empty"
    return "{}.{}.{}".format(BASE_FIELD_TOPIC, message_bus_id, app_id)


def field_message_bus_agent_topic(message_bus_id, agent_id=None):
    """ Utility method for getting the publish/subscribe topic for a specific message bus.

    :param message_bus_id:
    :param agent_id:
    :return:
    """
    assert message_bus_id, "message_bus_id cannot be empty"
    return "{}.{}.{}".format(BASE_FIELD_TOPIC, message_bus_id, agent_id)


def field_agent_request_queue(message_bus_id, agent_id):
    """ Utility method for getting the request topic for a specific distributed agent

    :param message_bus_id:
    :param agent_id:
    :return:
    """
    assert message_bus_id, "message_bus_id cannot be empty"
    return "{}.request.{}.{}".format(BASE_FIELD_QUEUE, message_bus_id, agent_id)


def context_request_queue(message_bus_id):
    """ Utility method for getting the request topic for context manager

    :param message_bus_id:
    :return:
    """
    assert message_bus_id, "message_bus_id cannot be empty"

    return "{}.request.{}.{}".format(BASE_FIELD_QUEUE, message_bus_id,
                                     message_bus_id + '.context_manager')


def field_output_topic(message_bus_id=None, simulation_id=None):
    """ Utility method for getting the field output topic.
    If message_bus_id is None, it returns topic used by centralized device interfaces to publish measurements.
    If message_bus_id is not None, it returns topic used by distributed devices interfaces to publish measurements which is then subscribed by distributed agents.

    :param message_bus_id:
    :param simulation_id
    :return: str: Topic to receive field measurements
    """

    if simulation_id is None:
        return "{}.{}".format(BASE_FIELD_TOPIC, "output")
    else:
        return "{}.{}.{}.{}".format(BASE_FIELD_TOPIC, "simulation.output", simulation_id,
                                    message_bus_id)


def field_input_topic(message_bus_id=None, simulation_id=None):
    """ Utility method for getting the field input topic.
    If message_bus_id is None, it returns topic used by centralized device interfaces to subscribe to control commands.
    If message_bus_id is not None, it returns topic used by distributed devices interfaces to subscribe to control commands.

    :param message_bus_id:
    :param simulation_id
    :return: str: Topic to receive input control commands
    """

    if simulation_id is None:
        return "{}.{}".format(BASE_FIELD_TOPIC, "input")
    else:
        return "{}.{}.{}.{}".format(BASE_FIELD_TOPIC, "simulation.input", simulation_id,
                                    message_bus_id)
