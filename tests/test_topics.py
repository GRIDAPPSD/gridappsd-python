import pytest
from gridappsd.topics import (service_input_topic, service_output_topic,
                              application_input_topic, application_output_topic)


def test_input_output_assertions():

    funcs = (service_input_topic, service_output_topic, application_output_topic, application_input_topic)

    for fn in funcs:
        with pytest.raises(AssertionError):
            fn(None, 5)
        with pytest.raises(AssertionError):
            fn("fncs", None)
        with pytest.raises(AssertionError):
            fn("", "")
        with pytest.raises(AssertionError):
            fn("", 5)
        with pytest.raises(AssertionError):
            fn(None, None)

