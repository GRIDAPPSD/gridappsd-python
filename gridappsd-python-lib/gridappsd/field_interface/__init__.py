import logging
import sys
import warnings

_log = logging.getLogger(__name__)

# These will be populated if gridappsd-field-bus is installed
context = None
context_managers = None
agents = None
field_proxy_forwarder = None
gridappsd_field_bus = None
interfaces = None

try:
    import gridappsd_field_bus.field_interface.context as _context
    import gridappsd_field_bus.field_interface.context_managers as _context_managers
    import gridappsd_field_bus.field_interface as _field_interface
    import gridappsd_field_bus.field_interface.agents as _agents
    import gridappsd_field_bus.field_interface.gridappsd_field_bus as _gridappsd_field_bus
    import gridappsd_field_bus.field_interface.interfaces as _interfaces

    # Expose as module attributes for `from gridappsd.field_interface import X` syntax
    context = _context
    context_managers = _context_managers
    agents = _agents
    gridappsd_field_bus = _gridappsd_field_bus
    interfaces = _interfaces

    # Also register in sys.modules for backwards compatibility
    sys.modules["gridappsd.field_interface.interfaces"] = _interfaces
    sys.modules["gridappsd.field_interface.context"] = _context
    sys.modules["gridappsd.field_interface.context_managers"] = _context_managers
    sys.modules["gridappsd.field_interface.agents"] = _agents
    sys.modules["gridappsd.field_interface.gridappsd_field_bus"] = _gridappsd_field_bus

    # field_proxy_forwarder has optional dependencies that may not be available
    try:
        import gridappsd_field_bus.field_interface.field_proxy_forwarder as _field_proxy_forwarder

        field_proxy_forwarder = _field_proxy_forwarder
        sys.modules["gridappsd.field_interface.field_proxy_forwarder"] = _field_proxy_forwarder
    except ImportError:
        _log.debug("field_proxy_forwarder not available (missing optional dependencies)")

    warnings.warn(
        message="gridappsd.field_interface is deprecated and will be removed in a future release. "
        "Use gridappsd_field_bus.field_interface instead.",
        category=DeprecationWarning,
    )
except ImportError as e:
    _log.error(f"Could not import field_interface: {e}. Install gridappsd-field-bus to get those functions.")
