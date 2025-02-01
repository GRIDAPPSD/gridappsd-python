

def test_modules_are_the_same():
    from gridappsd.field_interface import interfaces
    from gridappsd.field_interface import context_manager
    from gridappsd.field_interface import context
    from gridappsd.field_interface import agents
    from gridappsd.field_interface import gridappsd_field_bus

    from gridappsd_field_bus.field_interface import interfaces as field_bus_interfaces
    from gridappsd_field_bus.field_interface import context_manager as field_context_manager
    from gridappsd_field_bus.field_interface import context as field_context
    from gridappsd_field_bus.field_interface import agents as field_agents
    from gridappsd_field_bus.field_interface import gridappsd_field_bus as field_gridappsd_field_bus

    assert interfaces == field_bus_interfaces
    assert context_manager == field_context_manager
    assert context == field_context
    assert agents == field_agents
    assert gridappsd_field_bus == field_gridappsd_field_bus



