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

"""
Created on March 1, 2018

@author: Craig Allwardt
"""

from datetime import datetime
import inspect
import json
import logging
import random
from time import sleep

from stomp import Connection12 as Connection

_log = logging.getLogger(inspect.getmodulename(__file__))


class TimeoutError(Exception):
    pass


class GOSS(object):
    """ Base class providing connections to a GOSS instance via stomp protocol
    """

    def __init__(self, username='system', password='manager',
                 stomp_address='localhost', stomp_port='61613',
                 attempt_connection=True):
        self.__user = username
        self.__pass = password
        self.stomp_address = stomp_address
        self.stomp_port = stomp_port
        self._conn = None
        self._ids = set()
        self._topic_set = set()

        if attempt_connection:
            self._make_connection()

    @property
    def connected(self):
        return self._conn is not None

    def connect(self):
        self._make_connection()

    def disconnect(self):
        if self._conn:
            self._conn.disconnect()

        self._conn = None

    def send(self, topic, message):
        self._make_connection()
        _log.debug("Sending topic: {} body: {}".format(topic, message))
        self._conn.send(body=message, destination=topic, headers={'reply-to': '/temp-queue/goss.response'} )

    def get_response(self, topic, message, timeout=5):
        id = datetime.now().strftime("%Y%m%d%h%M%S")
        reply_to = "/temp-queue/response.{}".format(id)

        # Change message to string if we have a dictionary.
        if isinstance(message, dict):
            message = json.dumps(message)

        class ResponseListener(object):
            def __init__(self, topic):
                self.response = None
                self._topic = topic

            def on_message(self, header, message):
                if header['destination'] == self._topic:
                    _log.debug("Internal on message is: {} {}".format(header, message))
                    try:
                        self.response = json.loads(message) #dict(header=header, message=message)
                    except ValueError:
                        self.response = dict(error="Invalid json returned",
                                             header=header,
                                             message=message)

        listener = ResponseListener(reply_to)
        self.subscribe(reply_to, listener)

        self._conn.send(body=message, destination=topic, headers={'reply-to': reply_to})
        count = 0

        while count < timeout:
            if listener.response is not None:
                return listener.response

            sleep(1)
            count += 1

        self._conn.unsubscribe(id)

        raise TimeoutError("Request not responded to in a timely manner!")

    def subscribe(self, topic, callback):
        id = str(random.randint(1,1000000))
        while id in self._ids:
            id = str(random.randint(1, 1000000))

        if not callback:
            err = "Invalid callback specified in subscription"
            _log.error(err)
            raise AttributeError(err)
        if not topic:
            err = "Invalid topic specified in subscription"
            _log.error(err)
            raise AttributeError(err)

        self._make_connection()

        # Handle the case where callback is a function.
        if callable(callback):
            self._conn.set_listener(topic, CallbackWrapperListener(callback, id))
        else:
            self._conn.set_listener(topic, callback)
        self._conn.subscribe(destination=topic, ack='auto', id=id)

    def _make_connection(self):
        if self._conn is None or not self._conn.is_connected():
            _log.debug("Creating connection")
            self._conn = Connection([(self.stomp_address, self.stomp_port)])
            self._conn.connect(self.__user, self.__pass)
            self._conn.transport.wait_for_connection(5)


class CallbackWrapperListener(object):

    def __init__(self, callback, subscription):
        self._callback = callback
        self._subscription_id = subscription

    def on_message(self, header, message):
        if header['subscription'] == self._subscription_id:
            self._callback(header, message)
