import stomp
import json
import time
from typing import Callable, Dict
from gridappsd import GridAPPSD
from gridappsd import topics

REQUEST_FIELD = ".".join((topics.PROCESS_PREFIX, "request.field"))

class FieldListener:

    def __init__(self, ot_connection: GridAPPSD, proxy_connection: stomp.Connection):
        self.ot_connection = ot_connection
        self.proxy_connection = proxy_connection

    def on_message(self, headers, message):
        "Receives messages coming from Proxy bus (e.g. ARTEMIS) and forwards to OT bus"
        try:
            print(f"Received message at Proxy: {message}")

            if headers["destination"] == topics.field_output_topic():
                self.ot_connection.send(topics.field_output_topic(), message)

            elif headers["destination"] == topics.field_input_topic():
                pass

            elif headers["destination"] == REQUEST_FIELD:
                request_data = json.loads(message)
                request_type = request_data.get("request_type")
                if request_type == "get_context":
                    response = self.ot_connection.get_response(headers["destination"],message)
                    self.proxy_connection.send(headers["reply_to"],response)

            else:
                print(f"Unrecognized message received by Proxy: {message}")

        except Exception as e:
            print(f"Error processing message: {e}")

class FieldProxyForwarder:
    """
    FieldProxyForwarder acts as a bridge between field bus and OT bus
    when direct connection is not possible.
    """

    def __init__(self, connection_url: str, username: str, password: str):

        #Connect to OT
        self.ot_connection = GridAPPSD()

        #Connect to proxy
        self.broker_url = connection_url
        self.username = username
        self.password = password
        self.proxy_connection = stomp.Connection([(self.broker_url.split(":")[0], int(self.broker_url.split(":")[1]))],keepalive=True)
        self.proxy_connection.set_listener('', FieldListener(self.ot_connection, self.proxy_connection))
        self.proxy_connection.connect(self.username, self.password, wait=True)
        print('Connected to Proxy')



        #Subscribe to messages from field
        self.proxy_connection.subscribe(destination=topics.BASE_FIELD_TOPIC+'.*', id=1, ack="auto")

        #Subscribe to messages on OT bus
        self.ot_connection.subscribe(topics.field_input_topic(), self.on_message_from_ot)

    def on_message_from_ot(self, headers, message):
        "Receives messages coming from OT bus (GridAPPS-D) and forwards to Proxy bus"
        try:
            print(f"Received message from OT: {message}")

            if headers["destination"] == topics.field_input_topic():
                self.proxy_connection.send(topics.field_input_topic(), message)

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
    opts = parser.parse_args()
    proxy_connection_url = opts.connection_url
    proxy_username = opts.username
    proxy_password = opts.passwd

    proxy_forwarder = FieldProxyForwarder(proxy_connection_url, proxy_username, proxy_password)

    while True:
        time.sleep(0.1)
