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
        print("function headers: {}\nmessage: {}".format(headers, message))

    gapps = GridAPPSD(stomp_address="127.0.0.1",
                      stomp_port=61613,
                      username='system',
                      password='manager')

    gapps.subscribe('/topic/foo', on_message)
    sleep(1)
    gapps.send('/topic/foo', json.dumps(dict(bim='bash')))


    resp = gapps.get_platform_status()
    _log.debug("Got response of: {}".format(resp))

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
    print("RESP 2" + "*" * 20)
    resp2 = gapps.query_data(sparql)
    pprint(resp2)

    print("RESP 3" + "*" * 20)
    resp3 = gapps.query_model_names()
    pprint(resp3)

    print("RESP 4" + "*" * 20)
    resp4 = gapps.query_object_types()
    pprint(resp4)

    count = 0
    while count < 30:
        sleep(1)
        count += 1

    print("complete")