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

import calendar
from uuid import uuid4
import time


class DifferenceBuilder(object):
    """ Automates the building of forward and reverse cim differences

    """

    def __init__(self, simulation_id: str | int | None = None):

        self._simulation_id = simulation_id
        self._forward: list[dict] = []
        self._reverse: list[dict] = []

    def add_difference(self, object_id, attribute, forward_value, reverse_value):
        """ Add forward and reverse unit for an object attribute.

         All of the parameters must be serializable for sending the GOSS message bus.
         """
        forward = dict(object=object_id, attribute=attribute, value=forward_value)
        reverse = dict(object=object_id, attribute=attribute, value=reverse_value)
        self._forward.append(forward)
        self._reverse.append(reverse)

    def clear(self):
        """ Clear the forward and reverse differences """
        self._forward = []
        self._reverse = []

    def get_message(self, epoch=None):
        """ Get the message to send to the GOSS message bus

        :param epoch: The epoch time to use for the message timestamp.  If None, the current time (GMT) is used.
        """
        if epoch is None:
            epoch = calendar.timegm(time.gmtime())
        msg = dict(command="update",
                   input=dict(message=dict(timestamp=epoch,
                                           difference_mrid=str(uuid4()),
                                           reverse_differences=self._reverse,
                                           forward_differences=self._forward)))
        if self._simulation_id is not None:
            msg['input']['simulation_id'] = self._simulation_id
        return msg.copy()
