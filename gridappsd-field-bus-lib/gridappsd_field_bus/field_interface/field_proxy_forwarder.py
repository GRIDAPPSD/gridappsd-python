import stomp
import json
import time
from typing import Callable, Dict
from gridappsd import GridAPPSD
from gridappsd import topics

from cimgraph.databases import GridappsdConnection, BlazegraphConnection
from cimgraph.models import BusBranchModel, FeederModel

import os
import cimgraph.utils as utils
import cimgraph.data_profile.cimhub_ufls as cim

REQUEST_FIELD = ".".join((topics.PROCESS_PREFIX, "request.field"))

class FieldListener:

    def __init__(self, ot_connection: GridAPPSD, proxy_connection: stomp.Connection):
        self.ot_connection = ot_connection
        self.proxy_connection = proxy_connection

    def on_message(self, headers, message):
        "Receives messages coming from Proxy bus (e.g. ARTEMIS) and forwards to OT bus"
        try:
            print(f"Received message at Proxy. destination: {headers['destination']}, message: {headers}")

            if headers["destination"] == topics.field_output_topic():
                self.ot_connection.send(topics.field_output_topic(), message)

            elif headers["destination"] == topics.field_input_topic():
                pass

            elif headers["destination"] == REQUEST_FIELD:
                request_data = json.loads(message)
                request_type = request_data.get("request_type")
                if request_type == "get_context":
                    response = self.ot_connection.get_response(headers["destination"],message)
                    self.proxy_connection.send(headers["reply-to"],response)
                elif request_type == "start_publishing":
                    response = self.ot_connection.get_response(headers["destination"],message)
                    self.proxy_connection.send(headers["reply-to"],json.dumps(response))
            
            else:
                print(f"Unrecognized message received by Proxy: {message}")

        except Exception as e:
            print(f"Error processing message: {e}")

class FieldProxyForwarder:
    """
    FieldProxyForwarder acts as a bridge between field bus and OT bus
    when direct connection is not possible.
    """

    def __init__(self, connection_url: str, username: str, password: str, mrid :str):

        #Connect to OT
        self.ot_connection = GridAPPSD()

        #Connect to proxy
        self.broker_url = connection_url
        self.username = username
        self.password = password
        self.proxy_connection = stomp.Connection([(self.broker_url.split(":")[0], int(self.broker_url.split(":")[1]))],keepalive=True, heartbeats=(10000,10000))
        self.proxy_connection.set_listener('', FieldListener(self.ot_connection, self.proxy_connection))
        self.proxy_connection.connect(self.username, self.password, wait=True)
        
        print('Connected to Proxy')



        #Subscribe to messages from field
        self.proxy_connection.subscribe(destination=topics.BASE_FIELD_TOPIC+'.*', id=1, ack="auto")
        self.proxy_connection.subscribe(destination='goss.gridappsd.process.request.*', id=2, ack="auto")
        
        #Subscribe to messages on OT bus
        self.ot_connection.subscribe(topics.field_input_topic(), self.on_message_from_ot)



        os.environ['CIMG_CIM_PROFILE'] = 'cimhub_ufls'
        os.environ['CIMG_URL'] = 'http://localhost:8889/bigdata/namespace/kb/sparql'
        os.environ['CIMG_DATABASE'] = 'powergridmodel'
        os.environ['CIMG_NAMESPACE'] = 'http://iec.ch/TC57/CIM100#'
        os.environ['CIMG_IEC61970_301'] = '8'
        os.environ['CIMG_USE_UNITS'] = 'False'

        self.database = BlazegraphConnection()
        distribution_area = cim.DistributionArea(mRID=mrid)
        self.network = BusBranchModel(
            connection=self.database,
            container=distribution_area,
            distributed=False)
        self.network.get_all_edges(cim.DistributionArea)
        self.network.get_all_edges(cim.Substation)

        for substation in self.network.graph.get(cim.Substation,{}).values():
            print(f'Subscribing to Substation: /topic/goss.gridappsd.field.{substation.mRID}')
            self.ot_connection.subscribe('/topic/goss.gridappsd.field.'+substation.mRID, self.on_message_from_ot)



        #self.ot_connection.subscribe(topics.BASE_FIELD_TOPIC, self.on_message_from_ot)


    def on_message_from_ot(self, headers, message):

        "Receives messages coming from OT bus (GridAPPS-D) and forwards to Proxy bus"
        try:
            print(f"Received message from OT: {message}")

            if headers["destination"] == topics.field_input_topic():
                self.proxy_connection.send(topics.field_input_topic(),json.dumps(message))

            elif 'goss.gridappsd.field' in headers["destination"]:

                self.proxy_connection.send(headers["destination"],json.dumps(message))
            else:
                print(f"Unrecognized message received by OT: {message}")

        except Exception as e:
            print(f"Error processing message: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog="TestForwarder")
    parser.add_argument("username")
    parser.add_argument("passwd")
    parser.add_argument("connection_url")
    parser.add_argument("mrid")
    opts = parser.parse_args()
    proxy_connection_url = opts.connection_url
    proxy_username = opts.username
    proxy_password = opts.passwd
    mrid = opts.mrid

    proxy_forwarder = FieldProxyForwarder(proxy_connection_url, proxy_username, proxy_password, mrid)

    while True:
        time.sleep(0.1)
