import logging
import sys
from time import sleep

from gridappsd import GridAPPSD

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                    format="'%(asctime)s: %(name)-20s - %(levelname)-6s - %(message)s")

_log = logging.getLogger("gridappsd.__main__")


if __name__ == '__main__':

    class Listener(object):
        def on_message(self, headers, message):
            print("headers: {}\nmessage: {}".format(headers, message))
    conn = GridAPPSD(stomp_address="127.0.0.1",
                     stomp_port=61613,
                     username='system',
                     password='manager')

    conn.subscribe(topic='/topic/goss.>', callback=Listener())

    resp = conn.get_platform_status()
    _log.debug("Got response of: {}".format(resp))

    while True:
        sleep(1)