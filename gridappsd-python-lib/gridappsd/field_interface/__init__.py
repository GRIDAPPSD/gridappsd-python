import logging
import warnings
import gridappsd
_log = logging.getLogger(__name__)

try:
    from gridappsd_field_bus.field_interface import (
        interfaces,
        context,
        context_manager,
        gridappsd_field_bus,
        agents)


    warnings.warn(message="gridappsd.field_interface is deprecated and will be removed in a future release. Use gridappsd_field_bus.field_interface instead.",
                  category=DeprecationWarning)
except ImportError:
    _log.error("Could not import field_interface install gridappsd-field-bus to get those functions.")