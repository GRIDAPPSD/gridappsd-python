# import json
from gridappsd import topics, json_extension as json
from typing import Optional


class Query:
    """Class to create and execute request to query timeseries data"""

    def __init__(self, measurement):
        self.queryMeasurement = measurement
        self.queryFilter = []
        self.selectCriteria = []
        self.key = None

    def select(self, *keys):
        """Defines what fields should be returned from the query.

        If this function is not called or is called without argument then
        all the fields are returned.

        :param keys: list of fields to be returned
        """
        for key in keys:
            self.selectCriteria.append(key)
        return self

    def first(self, n=Optional[int]):
        """Method to add request to return first or oldest data to the query.

        When n is specified, query will return first or oldest 'n' rows.

        :param n:
        """
        if n is not None:
            self.first = n
        return self

    def last(self, n=Optional[int]):
        """Method to add request to return last or latest data to the query.

        When n is specified, query will return last or latest 'n' rows.

        :param n:
        """
        if n is not None:
            self.last = n
        return self

    def _add_filter(self, operator, value):
        """Append a single {key, operator: value} filter for the current key.

        :param operator: one of "ge", "le", "eq"
        :param value: value to filter on
        """
        if self.key is None:
            raise ValueError("Key is not specified. Call where_key first.")
        self.queryFilter.append({"key": self.key, operator: value})
        return self

    def ge(self, value):
        """Method to add 'value greater than or equal to' filter to a key.

        :param value:
        """
        return self._add_filter("ge", value)

    def le(self, value):
        """Method to add 'value less than or equal to' filter to a key.

        :param value:
        """
        return self._add_filter("le", value)

    def eq(self, value):
        """Method to add 'value equal to' filter to a key.

        :param value:
        """
        return self._add_filter("eq", value)

    def between(self, value1, value2):
        """Method to add 'value between' value1 and value2 filter to a key.

        :param value1: defines 'greater than equal to' filter for key's value
        :param value2: defines 'less than equal to' filter for key's value
        """
        self._add_filter("ge", value1)
        return self._add_filter("le", value2)

    def where_key(self, key):
        self.key = key
        return self

    def execute(self, gridappsd_obj):
        del self.key
        response = gridappsd_obj.get_response(topics.REQUEST_TIMESERIES_DATA, json.dumps(self.__dict__))
        return response
