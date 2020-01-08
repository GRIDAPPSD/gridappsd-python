import pytest
from contextlib import contextmanager
from gridappsd import GridAPPSD
from csv import DictWriter
from gridappsd.houses import house_keys

@contextmanager
def gappsd():
    g = GridAPPSD()
    yield g
    g.disconnect()


def test_multiple_calls_gets_same_houses_obj():
    with gappsd() as g:
        houses = g.get_houses()
        id_of_houses = id(houses)
        houses_again = g.get_houses()
        assert id_of_houses == id(houses_again)


def test_can_get_transactive_houses():
    with gappsd() as g:

        houses = g.get_houses().get_houses_for_feeder('_503D6E20-F499-4CC7-8051-971E23D0BF79')
        assert houses
        #
        # with open("testdatafile.csv", 'w') as fp:
        #     writer = DictWriter(fp, fieldnames=house_keys)
        #     writer.writeheader()
        #     for k, v in houses.items():
        #         writer.writerow(v._asdict())
