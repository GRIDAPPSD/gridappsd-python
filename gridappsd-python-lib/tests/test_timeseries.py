"""Unit tests for gridappsd.timeseries.Query filter building.

ge/le/eq/between all delegate to the shared _add_filter helper. These
tests assert the exact queryFilter list contents and ordering produced,
and that a filter method called before where_key raises.
"""

import pytest

from gridappsd.timeseries import Query


class TestAddFilter:
    def test_ge_appends_ge_filter_for_current_key(self):
        query = Query("measurement").where_key("value")

        query.ge(10)

        assert query.queryFilter == [{"key": "value", "ge": 10}]

    def test_le_appends_le_filter_for_current_key(self):
        query = Query("measurement").where_key("value")

        query.le(20)

        assert query.queryFilter == [{"key": "value", "le": 20}]

    def test_eq_appends_eq_filter_for_current_key(self):
        query = Query("measurement").where_key("value")

        query.eq(15)

        assert query.queryFilter == [{"key": "value", "eq": 15}]

    def test_between_appends_ge_then_le_in_order(self):
        query = Query("measurement").where_key("value")

        query.between(10, 20)

        assert query.queryFilter == [
            {"key": "value", "ge": 10},
            {"key": "value", "le": 20},
        ]

    def test_chained_filters_on_different_keys_preserve_each_keys_filters(self):
        query = Query("measurement")
        query.where_key("value").ge(10)
        query.where_key("timestamp").le(999)

        assert query.queryFilter == [
            {"key": "value", "ge": 10},
            {"key": "timestamp", "le": 999},
        ]

    def test_filter_without_where_key_raises_value_error(self):
        query = Query("measurement")

        with pytest.raises(ValueError):
            query.ge(10)

    def test_filter_methods_return_self_for_chaining(self):
        query = Query("measurement").where_key("value")

        result = query.ge(10)

        assert result is query
