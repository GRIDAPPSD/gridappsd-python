
#
# def test_multiple_calls_gets_same_houses_obj(gridappsd_client):
#     gapps = gridappsd_client
#     houses = gapps.get_houses()
#     id_of_houses = id(houses)
#     houses_again = gapps.get_houses()
#     assert id_of_houses == id(houses_again)


def test_can_get_transactive_houses(gridappsd_client):

    houses = gridappsd_client.get_houses().get_houses_for_feeder('_503D6E20-F499-4CC7-8051-971E23D0BF79')
    assert houses
