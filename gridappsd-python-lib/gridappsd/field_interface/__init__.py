import logging
import sys

_log = logging.getLogger(__name__)

try:
    import warnings

    import gridappsd_field_bus.field_interface.context as _context
    import gridappsd_field_bus.field_interface.context_managers as _context_managers
    import gridappsd_field_bus.field_interface as _field_interface
    import gridappsd_field_bus.field_interface.agents as _agents
    import gridappsd_field_bus.field_interface.field_proxy_forwarder as _field_proxy_forwarder
    import gridappsd_field_bus.field_interface.gridappsd_field_bus as _gridappsd_field_bus
    import gridappsd_field_bus.field_interface.interfaces as _interfaces

    sys.modules['gridappsd.field_interface'] = _field_interface
    sys.modules['gridappsd.field_interface.interfaces'] = _interfaces
    sys.modules['gridappsd.field_interface.context_managers'] = _context_managers
    sys.modules['gridappsd_.context_managers'] = _context_managers
    sys.modules['gridappsd.field_interface.agents'] = _agents
    sys.modules['gridappsd.field_interface.field_proxy_forwarder'] = _field_proxy_forwarder
    sys.modules['gridappsd.field_interface.gridappsd_field_bus'] = _gridappsd_field_bus





    warnings.warn(message="gridappsd.field_interface is deprecated and will be removed in a future release. Use gridappsd_field_bus.field_interface instead.",
                  category=DeprecationWarning)
except ImportError:
    _log.error("Could not import field_interface install gridappsd-field-bus to get those functions.")
