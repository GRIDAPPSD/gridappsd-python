

def test_modules_are_the_same():
    import sys

    # Note these are dynamically loaded please use gridappsd_field_bus packages instead.
    from gridappsd.field_interface import interfaces
    from gridappsd.field_interface import context
    from gridappsd.field_interface import context_managers
    from gridappsd.field_interface import agents
    from gridappsd.field_interface import gridappsd_field_bus

    from gridappsd_field_bus.field_interface import interfaces as field_bus_interfaces
    from gridappsd_field_bus.field_interface import context as field_context
    from gridappsd_field_bus.field_interface import context_managers as field_context_managers
    from gridappsd_field_bus.field_interface import agents as field_agents
    from gridappsd_field_bus.field_interface import gridappsd_field_bus as field_gridappsd_field_bus

    from gridappsd.field_interface.interfaces import FieldMessageBus
    from gridappsd_field_bus.field_interface.interfaces import FieldMessageBus as field_FieldMessageBus


    assert interfaces == field_bus_interfaces
    assert context_managers == field_context_managers
    assert context == field_context
    assert agents == field_agents
    assert gridappsd_field_bus == field_gridappsd_field_bus
    assert FieldMessageBus == field_FieldMessageBus