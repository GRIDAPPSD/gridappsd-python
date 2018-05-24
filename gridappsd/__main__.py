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
import json
import logging
from pprint import pprint, pformat
import sys
from time import sleep

from gridappsd import GridAPPSD

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                    format="'%(asctime)s: %(name)-20s - %(levelname)-6s - %(message)s")

logging.getLogger('stomp.py').setLevel(logging.WARNING)
_log = logging.getLogger("gridappsd.__main__")


if __name__ == '__main__':

    class Listener(object):
        def on_message(self, headers, message):
            print("headers: {}\nmessage: {}".format(headers, message))

    def on_message(headers, message):
        print("Received: headers: {}\nmessage: {}".format(headers, message))

    # Handle python 3 not having input_raw function.
    try:
        get_input = raw_input
    except NameError:
        get_input = input


    print("Creating GridAPPSD object")
    gapps = GridAPPSD(stomp_address="127.0.0.1",
                      stomp_port=61613,
                      username='system',
                      password='manager')

    print("Subscribing to /topic/foo")
    gapps.subscribe('/topic/foo', on_message)
    result = get_input("Press enter to send json.dumps(dict(bim='bash')) to topic /topic/foo")
    print("Sending data")
    gapps.send('/topic/foo', json.dumps(dict(bim='bash')))
    sleep(1)

    get_input("Press enter to receive platform status")
    resp = gapps.get_platform_status()
    pprint(resp)

    get_input("Press enter to query model info")
    resp = gapps.query_model_info()
    pprint(resp)

    get_input("Press enter to query model names")
    resp = gapps.query_model_names()
    pprint(resp)

    get_input("Press enter to query object types")
    resp = gapps.query_object_types()
    pprint(resp)

    get_input("Press enter to run ad-hoc query")
    # list all the connectivity nodes by feeder - CIMImporter when building GldNodes
    sparql = """
PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX c:  <http://iec.ch/TC57/2012/CIM-schema-cim17#>
SELECT ?feeder ?name WHERE {
 VALUES ?fdrid {"_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62"}  # 13 bus
 ?fdr c:IdentifiedObject.mRID ?fdrid.
 ?s c:ConnectivityNode.ConnectivityNodeContainer ?fdr.
 ?s r:type c:ConnectivityNode.
 ?s c:IdentifiedObject.name ?name.
 ?fdr c:IdentifiedObject.name ?feeder.
}
ORDER by ?feeder ?name
    """
    print("QUERY")
    print(sparql)
    print()
    resp = gapps.query_data(sparql)
    pprint(resp)

    get_input("Press enter to exit")
    print()
