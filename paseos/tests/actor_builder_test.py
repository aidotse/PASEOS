"""Tests to see if we can create satellites with different devices."""
import numpy as np
import pykep as pk
import sys

sys.path.append("../..")

from paseos import ActorBuilder

from test_utils import get_default_instance


def test_set_orbit():
    """Check if we can specify an orbit correctly"""
    _, sat1, earth = get_default_instance()
    ActorBuilder.set_orbit(sat1, [1000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)

    # check initial positions
    # r - position vector, v - velocity vector
    r, v = sat1.get_position_velocity(pk.epoch(0))
    assert np.isclose(r[0], 1000000)
    assert np.isclose(r[1], 0)
    assert np.isclose(r[2], 0)
    assert np.isclose(v[0], 0)
    assert np.isclose(v[1], 8000.0)
    assert np.isclose(v[2], 0)

    # check positions one second later
    r, v = sat1.get_position_velocity(pk.epoch(1 * pk.SEC2DAY))
    assert np.isclose(r[0], 999800.6897266058)
    assert np.isclose(r[1], 7999.468463301808)
    assert np.isclose(r[2], 0.0)
    assert np.isclose(v[0], -398.64065398803876)
    assert np.isclose(v[1], 7998.405250997527)
    assert np.isclose(v[2], 0.0)


def test_add_power_devices():
    """Check if we can add a power device"""
    _, sat1, _ = get_default_instance()
    ActorBuilder.set_power_devices(sat1, 42, 42, 42)
    assert sat1.battery_level_in_Ws == 42
    assert sat1.battery_level_ratio == 1
    assert sat1.charging_rate_in_W == 42


def test_add_comm_device():
    """Check if we can add a comm device"""
    _, sat1, _ = get_default_instance()
    ActorBuilder.add_comm_device(sat1, "dev1", 10)
    ActorBuilder.add_comm_device(sat1, "dev2", 42)

    assert len(sat1.communication_devices) == 2
    assert sat1.communication_devices["dev1"].bandwidth_in_kbps == 10
    assert sat1.communication_devices["dev2"].bandwidth_in_kbps == 42
