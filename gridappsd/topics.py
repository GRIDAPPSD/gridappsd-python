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
FNCS_BASE_INPUT_TOPIC = '/topic/goss.gridappsd.simulation.input'
FNCS_BASE_OUTPUT_TOPIC = '/topic/goss.gridappsd.simulation.output'
BASE_SIMULATION_TOPIC = '/topic/goss.gridappsd.simulation'
BASE_SIMULATION_STATUS_TOPIC = "/topic/goss.gridappsd.simulation.log"

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

REQUEST_REGISTER_APP = ".".join((PROCESS_PREFIX, "request.app.remote.register"))
REQUEST_APP_START = ".".join((PROCESS_PREFIX, "request.app.start"))
BASE_APPLICATION_HEARTBEAT = ".".join((BASE_TOPIC_PREFIX, "heartbeat"))


def service_input_topic(service_id, simulation_id):
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
    assert simulation_id, "simulation_id cannot be empty"
    return f"{BASE_SIMULATION_TOPIC}.{service_id}.{simulation_id}.input"


def service_output_topic(service_id, simulation_id):
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
    assert simulation_id, "Simulation id cannot be empty"
    return f"{BASE_SIMULATION_TOPIC}.{service_id}.{simulation_id}.output"


def application_input_topic(application_id, simulation_id):
    """ Utility method for getting the input topic for a specific application.

    The application_id should be the registered service with the platform.  One
    can get the list of registered application by using the `GridAPPSD.get_platform_status()`
    method with applications=True.

    :param application_id:
    :param simulation_id:
    :return:str: Topic to publish to for a specific application.
    """
    assert application_id, "application_id cannot be empty"
    assert simulation_id, "simulation_id cannot be empty"
    return f"{BASE_SIMULATION_TOPIC}.{application_id}.{simulation_id}.input"


def application_output_topic(application_id, simulation_id):
    """ Utility method for getting the output topic for a specific application.

    The application_id should be the registered service with the platform.  One
    can get the list of registered application by using the `GridAPPSD.get_platform_status()`
    method with applications=True.

    :param application_id:
    :param simulation_id:
    :return: str: Topic to subscribe to for application specific output.
    """
    assert application_id, "application_id cannot be empty"
    assert simulation_id, "simulation_id cannot be empty"
    return f"{BASE_SIMULATION_TOPIC}.{application_id}.{simulation_id}.output"


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
    return "{}.{}".format(BASE_SIMULATION_STATUS_TOPIC, simulation_id)


"""
//topics
	public static final String topic_prefix = "goss.gridappsd";

	//Process Manager topics
	public static final String topic_process_prefix = topic_prefix+".process";
	public static final String topic_request = topic_prefix+".process";



	//Process Manager Request Topics
	public static final String topic_requestSimulation = topic_process_prefix+".request.simulation";
	public static final String topic_requestData = topic_process_prefix+".request.data";
	public static final String topic_requestConfig = topic_process_prefix+".request.config";
	public static final String topic_requestApp = topic_process_prefix+".request.app";
	public static final String topic_requestSimulationStatus = topic_process_prefix+".request.status.simulation";
	public static final String topic_requestPlatformStatus = topic_process_prefix+".request.status.platform";


	public static final String topic_requestListAppsWithInstances = "goss.gridappsd.process.request.list.apps";
	public static final String topic_requestListServicesWithInstances = "goss.gridappsd.process.request.list.services";

	public static final String topic_responseData = topic_prefix+".response.data";

	public static final String topic_platformLog = topic_prefix+".platform.log";

	//App Request Topics
	public static final String topic_app_register = topic_requestApp+".register";
	public static final String topic_app_list = topic_requestApp+".list";
	public static final String topic_app_get = topic_requestApp+".get";
	public static final String topic_app_deregister = topic_requestApp+".deregister";
	public static final String topic_app_start = topic_requestApp+".start";
	public static final String topic_app_stop = topic_requestApp+".stop";
	public static final String topic_app_stop_instance = topic_requestApp+".stopinstance";


	//Configuration Manager topics
	public static final String topic_configuration = topic_prefix+".configuration";
	public static final String topic_configuration_powergrid = topic_configuration+".powergrid";
	public static final String topic_configuration_simulation = topic_configuration+".simulation";

	//Simulation Topics
	public static final String topic_simulation = topic_prefix+".simulation";
	public static final String topic_simulationInput = topic_simulation+".input";
	public static final String topic_simulationOutput = topic_simulation+".output";
	public static final String topic_simulationLog = topic_simulation+".log.";

	//Service Topics
	public static final String topic_service = topic_prefix+".simulation";
	public static final String topic_serviceInput = topic_service+".input";
	public static final String topic_serviceOutput = topic_service+".output";
	public static final String topic_serviceLog = topic_service+".log";

	//Application Topics
	public static final String topic_application = topic_prefix+".simulation";
	public static final String topic_applicationInput = topic_application+".input";
	public static final String topic_applicationOutput = topic_application+".output";
    public static final String topic_applicationLog = topic_application+".log";
"""
