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
from collections import defaultdict
import inspect
import json
import logging
import sys
import random
from time import sleep

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

import threading


from .utils import get_gridappsd_user, get_gridappsd_pass
from stomp import Connection12 as Connection
from stomp.exception import NotConnectedException

_log = logging.getLogger(inspect.getmodulename(__file__))


class TimeoutError(Exception):
    pass


class GOSS(object):
    """ Base class providing connections to a GOSS instance via stomp protocol
    """

    def __init__(self, username=None, password=None,
                 stomp_address='localhost', stomp_port='61613',
                 attempt_connection=True,
                 override_threading=None, stomp_log_level=logging.WARNING,
                 goss_log_level=logging.INFO):

        logging.getLogger('stomp.py').setLevel(stomp_log_level)
        logging.getLogger('goss').setLevel(goss_log_level)

        self.__user = username if username is not None else get_gridappsd_user()
        self.__pass = password if password is not None else get_gridappsd_pass()
        self.stomp_address = stomp_address
        self.stomp_port = stomp_port
        self._conn = None
        self._ids = set()
        self._topic_set = set()
        self._override_thread_fc = override_threading
        self._router_callback = CallbackRouter()

        if attempt_connection:
            self._make_connection()

    @property
    def connected(self):
        return self._conn is not None and self._conn.is_connected()

    def connect(self):
        self._make_connection()

    def disconnect(self):
        if self._conn:
            self._conn.disconnect()

        self._conn = None

    def override_threading(self, callback):
        self._override_thread_fc = callback

    def send(self, topic, message):
        self._make_connection()
        if isinstance(message, list) or isinstance(message, dict):
            message = json.dumps(message)
        _log.debug("Sending topic: {} body: {}".format(topic, message))
        self._conn.send(body=message, destination=topic,
                        headers={'GOSS_HAS_SUBJECT': True,
                                  'GOSS_SUBJECT': self.__user})
                                 
    def get_response(self, topic, message, timeout=5):
        id = datetime.now().strftime("%Y%m%d%h%M%S")
        reply_to = "/temp-queue/response.{}".format(id)

        # Change message to string if we have a dictionary.
        if isinstance(message, dict):
            message = json.dumps(message)
        elif isinstance(message, list):
            message = json.dumps(message)

        class ResponseListener(object):
            def __init__(self, topic):
                self.response = None
                self._topic = topic

            def on_message(self, header, message):

                _log.debug("Internal on message is: {} {}".format(header, message))
                try:
                    if isinstance(message, dict):
                        self.response = message
                    else:
                        self.response = json.loads(message)
                except ValueError:
                    self.response = dict(error="Invalid json returned",
                                         header=header,
                                         message=message)

            def on_error(self, headers, message):
                _log.error("ERR: {}".format(headers))
                _log.error("OUR ERROR: {}".format(message))

            def on_disconnect(self, header, message):
                _log.debug("Disconnected")

        listener = ResponseListener(reply_to)
        self.subscribe(reply_to, listener)

        self._conn.send(body=message, destination=topic,
                        headers={'reply-to': reply_to, 'GOSS_HAS_SUBJECT': True,
                                 'GOSS_SUBJECT': self.__user})
        count = 0

        while count < timeout:
            if listener.response is not None:
                break

            sleep(1)
            count += 1

        if listener.response is not None:
            return listener.response

        raise TimeoutError("Request not responded to in a timely manner!")

    def subscribe(self, topic, callback):
        """Subscribe to a given topic, and call callback on message.

        :param topic: topic to subscribe to. See topics.py.
        :param callback: function (callable) or class to be hit on
            every message. Note the class must have an "on_message"
            method. The function (or class's on_message method) will be
            passed two arguments: header and message.
        """
        conn_id = str(random.randint(1, 1000000))
        while conn_id in self._ids:
            conn_id = str(random.randint(1, 1000000))

        if not callback:
            err = "Invalid callback specified in subscription"
            _log.error(err)
            raise AttributeError(err)
        if not topic:
            err = "Invalid topic specified in subscription"
            _log.error(err)
            raise AttributeError(err)

        self._make_connection()

        if self._conn.get_listener('gridappsd') is None:
            self._conn.set_listener('gridappsd', self._router_callback)

        if callable(callback):
            self._router_callback.add_callback(topic, callback)
            # Handle the case where callback is a function
            # self._conn.set_listener(conn_id,
            #                         CallbackWrapperListener(callback, conn_id))
        else:
            # Case where the callback is (supposedly) a class.
            if not hasattr(callback, 'on_message'):
                m = "The given callback must have an 'on_message' method!"
                raise AttributeError(m)

            if not callable(callback.on_message):
                m = "The given callback's 'on_message' attribute must be " \
                    "callable!"
                raise TypeError(m)

            # Fix for https://github.com/GRIDAPPSD/GOSS-GridAPPS-D/issues/1072
            # register the onmessage from the passed listener object.  This is not
            # necessarily an ideal solution because we aren't also passing on the
            # other functions in the lifecycle, however this does pass the
            # test that was written so that listeners aren't called multiple times.
            self._router_callback.add_callback(topic, callback.on_message)
            # self._conn.set_listener(conn_id,
            #                         CallbackWrapperListener(callback.on_message, conn_id))

        _log.debug("Subscribing to {topic}".format(topic=topic))
        self._conn.subscribe(destination=topic, ack='auto', id=conn_id)

        return conn_id

    def unsubscribe(self, conn_id):
        self._conn.unsubscribe(conn_id)

    def _make_connection(self):
        if self._conn is None or not self._conn.is_connected():
            _log.debug("Creating connection")
            self._conn = Connection([(self.stomp_address, self.stomp_port)])
            if self._override_thread_fc is not None:
                self._conn.transport.override_threading(self._override_thread_fc)
            try:
                self._conn.connect(self.__user, self.__pass, wait=True)
            except TypeError as e:
                _log.error("TypeError: {e}".format(e=e))
            except NotConnectedException as e:
                _log.error("NotConnectedException: {e}".format(e=e))
            except AttributeError as e:
                _log.error("AttributeError: {e}".format(e=e))


class CallbackRouter(object):

    def __init__(self):
        self.callbacks = {}
        self._topics_callback_map = defaultdict(list)
        self._queue_callerback = Queue()
        self._thread = threading.Thread(target=self.run_callbacks)
        self._thread.daemon = True
        self._thread.start()

    def run_callbacks(self):
        _log.info("Starting thread queue")
        while True:
            cb, hdrs, msg = self._queue_callerback.get()
            try:
                msg = json.loads(msg)
            except:
                pass
                # msg = message

            for c in cb:
                c(hdrs, msg)
            sleep(0.01)

    def add_callback(self, topic, callback):
        if not topic.startswith('/topic/') and not topic.startswith('/temp-queue/'):
            topic = "/queue/{topic}".format(topic=topic)
        if callback in self._topics_callback_map[topic]:
            raise ValueError("Callbacks can only be used one time per topic")
        _log.debug("Added callbac using topic {topic}".format(topic=topic))
        self._topics_callback_map[topic].append(callback)

    def remove_callback(self, topic, callback):
        if topic in self._topics_callback_map:
            callbacks = self._topics_callback_map[topic]
            try:
                callbacks.remove(callback)
            except ValueError:
                pass

    def on_message(self, headers, message):
        destination = headers['destination']
        # _log.debug("Topic map keys are: {keys}".format(keys=self._topics_callback_map.keys()))
        if destination in self._topics_callback_map:
            self._queue_callerback.put((self._topics_callback_map[destination], headers, message))
        else:
            _log.error("INVALID DESTINATION {destination}".format(destination=destination))

    def on_error(self, header, message):
        _log.error("Error in callback router")
        _log.error(header)
        _log.error(message)
