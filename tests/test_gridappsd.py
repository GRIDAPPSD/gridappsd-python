from time import sleep

from gridappsd import topics


def test_get_model_info(gridappsd_client):
    """ The expecation is that we will have multiple models that we can retrieve from the
    database.  Two of which should have the model name of ieee8500 and ieee123.  The models
    should have the correct entry keys.
    """
    gappsd = gridappsd_client

    info = gappsd.query_model_info()

    node_8500 = None
    node_123 = None
    for info_def in info['data']['models']:
        if info_def['modelName'] == 'ieee8500':
            node_8500 = info_def
        elif info_def['modelName'] == 'ieee123':
            node_123 = info_def

    assert node_123, "Missing the 123 model"
    assert node_8500, "Missing 8500 node model."

    keys = ["modelName", "modelId", "stationName", "stationId", "subRegionName", "subRegionId",
            "regionName", "regionId"]
    correct_keys = set(keys)

    assert len(correct_keys) == len(node_123)
    assert len(correct_keys) == len(node_8500)

    for x in node_123:
        correct_keys.remove(x)

    assert len(correct_keys) == 0

    correct_keys = set(keys)

    for x in node_8500:
        correct_keys.remove(x)

    assert len(correct_keys) == 0


def test_listener_multi_topic(gridappsd_client):
    gappsd = gridappsd_client

    class Listener:
        def __init__(self):
            self.call_count = 0

        def reset(self):
            self.call_count = 0

        def on_message(self, headers, message):
            print("Message was: {}".format(message))
            self.call_count += 1

    listener = Listener()

    input_topic = topics.simulation_input_topic("5144")
    output_topic = topics.simulation_output_topic("5144")

    gappsd.subscribe(input_topic, listener)
    gappsd.subscribe(output_topic, listener)

    gappsd.send(input_topic, "Any message")
    sleep(1)
    assert 1 == listener.call_count
    listener.reset()
    gappsd.send(output_topic, "No big deal")
    sleep(1)
    assert 1 == listener.call_count