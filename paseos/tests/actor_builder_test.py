"""Tests to see if we can create satellites with different devices."""
import numpy as np
import pykep as pk
import sys

sys.path.append("../..")

from paseos import ActorBuilder, SpacecraftActor

from test_utils import get_default_instance


def test_set_TLE():
    """Check if we can set a TLE correctly"""

    _, sentinel2a, earth = get_default_instance()
    # Set the TLE
    line1 = "1 40697U 15028A   23188.15862373  .00000171  00000+0  81941-4 0  9994"
    line2 = "2 40697  98.5695 262.3977 0001349  91.8221 268.3116 14.30817084419867"
    ActorBuilder.set_TLE(sentinel2a, line1, line2)

    # Check that get_altitude returns a sensible value
    earth_radius = 6371000
    assert sentinel2a.get_altitude() > earth_radius + 780000
    assert sentinel2a.get_altitude() < earth_radius + 820000

    # Check that get_position_velocity returns sensible values
    position, velocity = sentinel2a.get_position_velocity(sentinel2a.local_time)
    assert position is not None
    assert velocity is not None

    # Create an actor with a keplerian orbit and check that the position and velocity
    # diverge over time
    s2a_kep = ActorBuilder.get_actor_scaffold("s2a_kep", SpacecraftActor, sentinel2a.local_time)
    ActorBuilder.set_orbit(s2a_kep, position, velocity, sentinel2a.local_time, earth)

    # After some orbits the differences should be significant
    # since the TLE uses SGP4 and the other actor uses Keplerian elements
    t0_later = pk.epoch(sentinel2a.local_time.mjd2000 + 1)
    r, v = sentinel2a.get_position_velocity(t0_later)
    r_kep, v_kep = s2a_kep.get_position_velocity(t0_later)
    print("r,v SGP4 after  1 day")
    print(r)
    print(v)
    print("r,v Kep  after  1 day")
    print(r_kep)
    print(v_kep)
    print("Differences in r and v")
    print(np.linalg.norm(np.array(r) - np.array(r_kep)))
    print(np.linalg.norm(np.array(v) - np.array(v_kep)))
    assert np.linalg.norm(np.array(r) - np.array(r_kep)) > 100000
    assert np.linalg.norm(np.array(v) - np.array(v_kep)) > 400


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
    assert sat1.state_of_charge == 1
    assert sat1.charging_rate_in_W == 42


def test_add_comm_device():
    """Check if we can add a comm device"""
    _, sat1, _ = get_default_instance()
    ActorBuilder.add_comm_device(sat1, "dev1", 10)
    ActorBuilder.add_comm_device(sat1, "dev2", 42)

    assert len(sat1.communication_devices) == 2
    assert sat1.communication_devices["dev1"].bandwidth_in_kbps == 10
    assert sat1.communication_devices["dev2"].bandwidth_in_kbps == 42


def test_set_spacecraft_body_model():
    """Check if we can set the spacecraft body model, and if the moments of inertia are calculated correctly"""
    _, sat1, _ = get_default_instance()
    ActorBuilder.set_spacecraft_body_model(sat1, mass=100)

    assert sat1.mass == 100
    assert all(sat1.body_center_of_gravity == np.array([0, 0, 0]))      # check the default mesh is centered
    assert sat1.body_mesh.volume == 1                                # check the default volume is correct
    assert round(sat1.body_moment_of_inertia[0, 0], 4) == 16.6667  # for the default mesh
    assert sat1.body_moment_of_inertia[0, 1] == 0.0                   # Should be zero if the mass distribution is even
