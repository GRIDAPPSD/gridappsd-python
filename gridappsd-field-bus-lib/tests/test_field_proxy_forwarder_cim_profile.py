import importlib

import pytest


@pytest.mark.parametrize("cim_profile", ["cimhub_2023"])
def test_field_proxy_forwarder_imports_cleanly_and_profile_has_required_types(cim_profile):
    """FieldProxyForwarder must import without raising ModuleNotFoundError, and
    the configured CIM profile module must expose DistributionArea and
    Substation, since FieldProxyForwarder.__init__ resolves both from it.
    """
    # Import the module under test. This must not raise ModuleNotFoundError,
    # which was the failure mode when the module imported the now-removed
    # cimhub_ufls profile unconditionally at module scope.
    from gridappsd_field_bus.field_interface import field_proxy_forwarder  # noqa: F401

    profile_module = importlib.import_module("cimgraph.data_profile." + cim_profile)

    assert hasattr(profile_module, "DistributionArea")
    assert hasattr(profile_module, "Substation")
