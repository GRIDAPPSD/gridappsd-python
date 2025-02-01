import stomp
import json
from typing import Callable, Dict
from gridappsd import GridAPPSD
from gridappsd import topics


class FieldProxyForwarder():
    """
    FieldProxyForwarder acts as a bridge between field bus and OT bus
    when direct connection is not possible.
    """

    def __init__(self, connection_url: str, username: str, password: str):

        #Connect to proxy
        self.broker_url = connection_url
        self.username = username
        self.password = password
        self.proxy_connection = stomp.Connection([(self.broker_url.split(":")[0],
                                                   int(self.broker_url.split(":")[1]))])
        self.proxy_connection.connect(self.username, self.password, wait=True)

        #Connect to OT
        self.ot_connection = GridAPPSD()

        #Subscribe to messages from field
        self.proxy_connection.set_listener('', self.on_message_from_field)
        self.proxy_connection.subscribe(destination=topics.BASE_FIELD_TOPIC, id=1, ack="auto")

        #Subscribe to messages on OT bus
        self.ot_connection.subscribe(topics.BASE_FIELD_TOPIC, self.on_message_from_ot)

    def on_message_from_ot(self, headers, message):
        "Receives messages coming from OT bus (GridAPPS-D) and forwards to Proxy bus"
        try:
            print(f"Received message from OT: {message}")

            if headers["destination"] == topics.field_input_topic():
                self.proxy_connection.send(topics.field_input_topic, message)

            elif "goss.gridappsd.field.simulation.output." in headers["destination"]:
                print("Simulation output received at OT. Ignoring.")

            else:
                print(f"Unrecognized message received by OT: {message}")

        except Exception as e:
            print(f"Error processing message: {e}")

    def on_message_from_field(self, headers, message):
        "Receives messages coming from Proxy bus (e.g. ARTEMIS) and forwards to OT bus"
        try:
            print(f"Received message at Proxy: {message}")

            if headers["destination"] == topics.field_output_topic():
                self.ot_connection.send(topics.field_output_topic, message)

            elif "context_manager" in headers["destination"]:
                request_data = json.loads(message)
                request_type = request_data.get("request_type")
                if request_type == "get_context":
                    response = self.ot_connection.get_response(headers["destination"], message)
                    self.proxy_connection.send(headers["reply_to"], response)

            else:
                print(f"Unrecognized message received by Proxy: {message}")

        except Exception as e:
            print(f"Error processing message: {e}")


if __name__ == "__main__":

    proxy_connection_url = "localhost:61613"
    proxy_username = "admin"
    proxy_password = "admin"

    proxy_forwarder = FieldProxyForwarder(proxy_connection_url, proxy_username, proxy_password)
