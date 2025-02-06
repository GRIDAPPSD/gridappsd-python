def test_initialization_with_and_without_simulation_id():
    from gridappsd.difference_builder import DifferenceBuilder

    # Test with simulation_id
    builder_with_id = DifferenceBuilder(simulation_id=12345)
    assert builder_with_id._simulation_id == 12345
    assert builder_with_id._forward == []
    assert builder_with_id._reverse == []

    # Test without simulation_id
    builder_without_id = DifferenceBuilder()
    assert builder_without_id._simulation_id is None
    assert builder_without_id._forward == []
    assert builder_without_id._reverse == []

def test_initialization_with_none_simulation_id():
    from gridappsd.difference_builder import DifferenceBuilder

    # Test with None as simulation_id
    builder_with_none = DifferenceBuilder(simulation_id=None)
    assert builder_with_none._simulation_id is None
    assert builder_with_none._forward == []
    assert builder_with_none._reverse == []


def test_returns_message_with_current_gmt_time_when_epoch_is_none():
    import calendar
    import time
    from uuid import UUID
    from gridappsd.difference_builder import DifferenceBuilder

    builder = DifferenceBuilder(simulation_id=None)
    result = builder.get_message(epoch=None)

    current_epoch = calendar.timegm(time.gmtime())
    assert abs(result['input']['message']['timestamp'] - current_epoch) < 2  # Allowing a small time difference
    assert isinstance(UUID(result['input']['message']['difference_mrid']), UUID)

def test_handles_empty_forward_differences_list():
    from gridappsd.difference_builder import DifferenceBuilder

    builder = DifferenceBuilder(simulation_id=None)
    builder._forward = []
    result = builder.get_message(epoch=1234567890)

    assert result['input']['message']['forward_differences'] == []


def test_adds_forward_and_reverse_differences():
    from gridappsd.difference_builder import DifferenceBuilder

    db = DifferenceBuilder()
    db.add_difference("obj1", "attr1", "forward_val", "reverse_val")

    assert db._forward == [{
        "object": "obj1",
        "attribute": "attr1",
        "value": "forward_val"
    }]
    assert db._reverse == [{
        "object": "obj1",
        "attribute": "attr1",
        "value": "reverse_val"
    }]


def test_handles_empty_strings():
    from gridappsd.difference_builder import DifferenceBuilder

    db = DifferenceBuilder()
    db.add_difference("", "", "forward_val", "reverse_val")

    assert db._forward == [{
        "object": "",
        "attribute": "",
        "value": "forward_val"
    }]
    assert db._reverse == [{
        "object": "",
        "attribute": "",
        "value": "reverse_val"
    }]
