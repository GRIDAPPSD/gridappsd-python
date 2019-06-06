from pprint import pprint

import pytest

from gridappsd import GridAPPSD


@pytest.fixture
def gappsd():

    gappsd = GridAPPSD()
    yield gappsd
    gappsd.disconnect()
    gappsd = None


def test_get_model_info(gappsd):
    """ The expecation is that we will have multiple models that we can retrieve from the
    database.  Two of which should have the model name of ieee8500 and ieee123.  The models
    should have the correct entry keys.
    """
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

