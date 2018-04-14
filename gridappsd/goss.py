# -------------------------------------------------------------------------------
# Copyright (c) 2017, Battelle Memorial Institute All rights reserved.
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
"""
Created on March 1, 2018

@author: Craig Allwardt
"""

import inspect
import logging
import os

from stomp import Connection12 as Connection, ConnectionListener, PrintingListener

import stomp
import yaml

_log = logging.getLogger(inspect.getmodulename(__file__))


class GOSS(object):

    def __init__(self, username='system', password='manager',
                 stomp_address='127.0.0.1', stomp_port='61613', id=1,
                 attempt_connection=True):
        self.__user = username
        self.__pass = password
        self.stomp_address = stomp_address
        self.stomp_port = stomp_port
        self._conn = None
        self._id = id

        if attempt_connection:
            self._make_connection()
        # simulation_id, 'system', 'manager', goss_server = '127.0.0.1', stomp_port = '61613'

    @property
    def connected(self):
        return self._conn is not None

    def connect(self):
        self._make_connection()

    def send(self, topic, message):
        self._make_connection()
        _log.debug("Sending topic: {} body: {}".format(topic, message))
        self._conn.send(body=message, destination=topic)
        # self._id += 1
        # if self._id > 10000:
        #     self._id = 1

    def subscribe(self, topic, callback):
        if not callback:
            err = "Invalid callback specified in subscription"
            _log.error(err)
            raise AttributeError(err)
        if not topic:
            err = "Invalid topic specified in subscription"
            _log.error(err)
            raise AttributeError(err)
        self._make_connection()
        self._conn.set_listener(topic, callback)
        self._conn.subscribe(destination=topic, ack='auto', id=self._id)

    def _make_connection(self):
        if self._conn is None or not self._conn.is_connected():
            _log.debug("Creating connection")
            self._conn = Connection([(self.stomp_address, self.stomp_port)])
            self._conn.connect(self.__user, self.__pass, wait=True)


class JSONResponseListener(ConnectionListener):

    def __init__(self, callback):
        super(JSONResponseListener, self).__init__()
        self._callback = callback

    def on_connecting(self, host_and_port):
        """
        :param (str,int) host_and_port:
        """
        _log.debug('on_connecting %s %s' % host_and_port)

    def on_connected(self, headers, body):
        """
        :param dict headers:
        :param body:
        """
        _log.debug('on_connected %s %s' % (headers, body))

    def on_disconnected(self):
        _log.debug('on_disconnected')

    def on_heartbeat_timeout(self):
        _log.debug('on_heartbeat_timeout')

    def on_before_message(self, headers, body):
        """
        :param dict headers:
        :param body:
        """
        _log.debug('on_before_message %s %s' % (headers, body))
        return headers, body

    def on_message(self, headers, body):
        """
        :param dict headers:
        :param body:
        """
        _log.debug('headers are dict: {}'.format(isinstance(headers, dict)))
        _log.debug('on_message %s %s' % (headers, body))
        self._callback(headers, body)

    def on_receipt(self, headers, body):
        """
        :param dict headers:
        :param body:
        """
        _log.debug('on_receipt %s %s' % (headers, body))

    def on_error(self, headers, body):
        """
        :param dict headers:
        :param body:
        """
        _log.debug('on_error %s %s' % (headers, body))

    def on_send(self, frame):
        """
        :param Frame frame:
        """
        _log.debug('on_send %s %s %s' % (frame.cmd, frame.headers, frame.body))

    def on_heartbeat(self):
        _log.debug('on_heartbeat')

# class JSONResponseListener(ConnectionListener):
#
#     def __init__(self, callback):
#         self._callback = callback
#
#     def on_message(self, headers, message):
#         print("{} {}".format(headers, message))
#         self._callback(headers, message)
#
#     def on_error(self, headers, message):
#         print("error: {} {}".format(headers, message))

#
# class GOSSListener(object):
#     def on_message(self, headers, msg):
#         message = {}
#         try:
#             message_str = 'received message ' + str(msg)
#             if fncs.is_initialized():
#                 _send_simulation_status('RUNNING', message_str, 'DEBUG')
#             else:
#                 _send_simulation_status('STARTED', message_str, 'DEBUG')
#             json_msg = yaml.safe_load(str(msg))
#             if json_msg['command'] == 'isInitialized':
#                 message_str = 'isInitialized check: ' + str(is_initialized)
#                 if fncs.is_initialized():
#                     _send_simulation_status('RUNNING', message_str, 'DEBUG')
#                 else:
#                     _send_simulation_status('STARTED', message_str, 'DEBUG')
#                 message['command'] = 'isInitialized'
#                 message['response'] = str(is_initialized)
#                 if (simulation_id != None):
#                     message['output'] = _get_fncs_bus_messages(simulation_id)
#                 message_str = 'Added isInitialized output, sending message ' + str(message) + ' connection ' + str(
#                     goss_connection)
#                 if fncs.is_initialized():
#                     _send_simulation_status('RUNNING', message_str, 'DEBUG')
#                 else:
#                     _send_simulation_status('STARTED', message_str, 'DEBUG')
#                 goss_connection.send(output_to_goss_topic, json.dumps(message))
#                 goss_connection.send(output_to_goss_queue, json.dumps(message))
#             elif json_msg['command'] == 'update':
#                 message['command'] = 'update'
#                 _publish_to_fncs_bus(simulation_id, json.dumps(json_msg['message']))  # does not return
#             elif json_msg['command'] == 'nextTimeStep':
#                 message_str = 'is next timestep'
#                 _send_simulation_status('RUNNING', message_str, 'DEBUG')
#                 message['command'] = 'nextTimeStep'
#                 current_time = json_msg['currentTime']
#                 message_str = 'incrementing to ' + str(current_time)
#                 _send_simulation_status('RUNNING', message_str, 'DEBUG')
#                 _done_with_time_step(
#                     current_time)  # current_time is incrementing integer 0 ,1, 2.... representing seconds
#                 message_str = 'done with timestep ' + str(current_time)
#                 _send_simulation_status('RUNNING', message_str, 'DEBUG')
#                 message_str = 'simulation id ' + str(simulation_id)
#                 _send_simulation_status('RUNNING', message_str, 'DEBUG')
#                 message['output'] = _get_fncs_bus_messages(simulation_id)
#                 response_msg = json.dumps(message)
#                 message_str = 'sending fncs output message ' + str(response_msg)
#                 _send_simulation_status('RUNNING', message_str, 'DEBUG')
#                 goss_connection.send(output_to_goss_topic, response_msg)
#                 goss_connection.send(output_to_goss_queue, response_msg)
#             elif json_msg['command'] == 'stop':
#                 message_str = 'Stopping the simulation'
#                 _send_simulation_status('stopped', message_str, 'INFO')
#                 fncs.die()
#                 sys.exit()
#
#         except Exception as e:
#             message_str = 'Error in command ' + str(e)
#             _send_simulation_status('ERROR', message_str, 'ERROR')
#             if fncs.is_initialized():
#                 fncs.die()
#
#     def on_error(self, headers, message):
#         message_str = 'Error in goss listener ' + str(message)
#         _send_simulation_status('ERROR', message_str, 'ERROR')
#         if fncs.is_initialized():
#             fncs.die()
#
#     def on_disconnected(self):
#         if fncs.is_initialized():
#             fncs.die()
