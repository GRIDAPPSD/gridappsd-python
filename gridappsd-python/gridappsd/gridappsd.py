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

import inspect
import json
import logging
from datetime import datetime
from logging import DEBUG, INFO, WARNING, FATAL, WARN
import time

from gridappsd.goss import GOSS
from gridappsd import utils
import gridappsd.topics as t
from gridappsd import ProcessStatusEnum
from gridappsd.houses import Houses
from gridappsd.loghandler import Logger, VALID_LOG_LEVELS, getNameToLevel

# from . configuration_types import ConfigurationType

_log = logging.getLogger(inspect.getmodulename(__file__))

POWERGRID_MODEL = "powergridmodel"


class InvalidSimulationIdError(Exception):
    pass


class GridAPPSD(GOSS):
    """ The main :class:`GridAPPSD` interface for connecting to a GridAPPSD instance
    """
    # TODO Get the caller from the traceback/inspect module.
    def __init__(self, simulation_id=None,
                 address=None, **kwargs):

        if address is None:
            address = utils.get_gridappsd_address()

        if 'stomp_address' in kwargs and 'stomp_port' in kwargs:
            address = (kwargs.pop('stomp_address'), kwargs.pop('stomp_port'))
        elif 'stomp_address' in kwargs and not 'stomp_port' in kwargs or \
             'stomp_port' in kwargs and not 'stomp_address' in kwargs:
            raise ValueError("If stomp_address is specified the so should stomp_port")

        super(GridAPPSD, self).__init__(
            stomp_address=address[0],
            stomp_port=address[1],
            **kwargs)
        self._houses = Houses(self)
        self._simulation_log_topic = None
        self._simulation_id = None
        # Transfer simulation_id from environment if its not passed
        # through the constructor.
        if simulation_id is None:
            simulation_id = utils.get_gridappsd_simulation_id()
        self._simulation_id = simulation_id
        self._process_status = ProcessStatusEnum("STARTING")
        if self._simulation_id:
            self._simulation_log_topic = t.simulation_log_topic(self._simulation_id)

    def get_logger(self) -> Logger:
        """
        Return a log instance for interacting with the log within the gridappsd platform

        :return: :class:`gridappsd.loghandler.Logger`
        """
        return Logger(self)

    def get_houses(self) -> Houses:
        return self._houses
    
    def get_simulation_id(self):
        """ 
        Return the simulation_id given to the GridAPPSD instance
        
        :return:
        """
        if not self._simulation_id:
            self._simulation_id = utils.get_gridappsd_simulation_id()
            if self._simulation_id:
                self._simulation_log_topic = t.simulation_log_topic(self._simulation_id)
        return self._simulation_id
    
    def set_application_status(self, status):
        """
        Set the application status.
        :param status:
        """
        try:
            self._process_status = ProcessStatusEnum(status)
        except ValueError:
            self.get_logger().warning("Unsuccessful change of application status."
                            + f"Valid statuses are {ProcessStatusEnum.__members__}.")

    def set_service_status(self, status):
        """
        Set the service status.
        :param status:
        """
        try:
            self._process_status = ProcessStatusEnum(status)
        except ValueError:
            self.get_logger().warning("Unsuccessful change of service status."
                                      + f"Valid statuses are {ProcessStatusEnum.__members__}.")

    def set_simulation_id(self, simulation_id):
        if simulation_id is None:
            self.get_logger().warning("None value for simulation_id set.")
        else:
            simulation_id = str(simulation_id)
            self._simulation_id = simulation_id
            self._simulation_log_topic = t.simulation_log_topic(self._simulation_id)

    def get_application_status(self):
        """
        Return the application status
        :return:
        """
        return self._process_status.value

    def get_application_id(self):
        return utils.get_gridappsd_application_id()
    
    def get_service_status(self):
        """
        Return the service status
        :return:
        """
        return self._process_status.value
    
    def query_object_types(self, model_id=None):
        """ Allows the caller to query the different object types.
                
        :param model_id:
        :return:
        """
        args = {}
        if model_id:
            args["modelId"] = model_id
        payload = self._build_query_payload("QUERY_OBJECT_TYPES", **args)
        return self.get_response(t.REQUEST_POWERGRID_DATA, payload, timeout=30)

    def query_model_names(self, model_id=None):
        args = {}
        if model_id is not None:
            args["modelId"] = model_id
        payload = self._build_query_payload("QUERY_MODEL_NAMES", **args)
        return self.get_response(t.REQUEST_POWERGRID_DATA, payload, timeout=30)

    def query_model_info(self):
        payload = self._build_query_payload("QUERY_MODEL_INFO")
        return self.get_response(t.REQUEST_POWERGRID_DATA, payload, timeout=30)
    
    def query_model(self, model_id=None, object_type=None, object_id=None, response_format='JSON'):
        args = {}
        if model_id is not None:
            args["modelId"] = model_id
        if object_type is not None:
            args["objectType"] = object_type
        if object_id is not None:
            args["objectId"] = object_id   
        if response_format is not None:
            args["resultFormat"] = response_format   
        payload = self._build_query_payload("QUERY_MODEL", **args)
        return self.get_response(t.REQUEST_POWERGRID_DATA, payload, timeout=30)

    def query_object(self, object_id, model_id=None):
        if not object_id:
            raise ValueError("Invalid object_id specified.")
        args = dict(objectId=object_id)
        if model_id is not None:
            args["modelId"] = model_id
        payload = self._build_query_payload("QUERY_OBJECT", **args)
        return self.get_response(t.REQUEST_POWERGRID_DATA, payload, timeout=30)
    
    def query_object_dictionary(self, model_id, object_type=None, object_id=None):
        if not model_id:
            raise ValueError("model_id is not specified.")
        if not object_id and not object_type:
            raise ValueError("No obejct_id or object_type specified.")
        args={}
        args["modelId"] = model_id
        if object_id is not None:
            args["objectId"] = object_id
        if object_type is not None:
            args["objectType"] = object_type
        payload = self._build_query_payload("QUERY_OBJECT_DICT", **args)
        return self.get_response(t.REQUEST_POWERGRID_DATA, payload, timeout=30)

    def query_data(self, query, database_type=POWERGRID_MODEL, timeout=30):
        request_type = None
        if database_type == POWERGRID_MODEL:
            request_type = 'QUERY'
        else:
            raise ValueError("Only supported {} currently".format(POWERGRID_MODEL))

        payload = self._build_query_payload(request_type, queryString=query)
        # Do this so we can eventually support other db through this mechanism.
        request_topic = '.'.join((t.REQUEST_DATA, database_type))
        return self.get_response(request_topic, json.dumps(payload), timeout=timeout)

    def get_platform_status(self, applications=True, services=True, appInstances=True, serviceInstances=True):
        _log.debug("Retrieving platform status from GridAPPSD")
        msg = dict(appInstances=appInstances, applications=applications, services=services,
                   serviceInstances=serviceInstances)
        return self.get_response(t.REQUEST_PLATFORM_STATUS, json.dumps(msg), timeout=30)

    def send_simulation_status(self, status, message, log_level=INFO):
        _log.debug("SEND SIM STATUS: {} message: {}".format(status, message))
        # Transform log level into something for use if we can.
        if isinstance(log_level, str):
            log_level = getNameToLevel(log_level)
        if log_level not in VALID_LOG_LEVELS:
            raise InvalidSimulationIdError("Invalid log_level specified!")
        if not self._simulation_log_topic:
            raise InvalidSimulationIdError()
        gad_log = self.get_logger()
        self.set_service_status(status)
        gad_log.log(message, log_level)

    def send_status(self, status, topic, log_level=INFO):
        self.set_application_status(status)
        status_message = self.build_message_json(self.get_application_status(),
            "", log_level)
        self.send(topic, status_message)

    def build_message_json(self, status, message, log_level):
        t_now = datetime.utcnow()
        status_message = {
            "source": utils.get_gridappsd_application_id(),
            "processId": f"{self._simulation_id}",
            "timestamp": int(time.mktime(t_now.timetuple()))*1000,
            "procesStatus": status,
            "logMessage": str(message),
            "logLevel": logging.getLevelName(log_level),
            "storeToDb": True
        }
        data = json.dumps(status_message)

        return data

    def _build_query_payload(self, request_type, response_format='JSON', **kwargs):
        d = dict(requestType=request_type, resultFormat=response_format)
        d.update(**kwargs)
        return d



