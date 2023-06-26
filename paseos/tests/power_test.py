"""This test checks whether power charging is performed correctly"""

from test_utils import get_default_instance

import paseos
from paseos import ActorBuilder, SpacecraftActor
from paseos.power.is_in_eclipse import is_in_eclipse

import pykep as pk


def test_power_charging():
    """Checks whether we can charge an actor"""
    sim, sat1, earth = get_default_instance()

    # Initial power is 500m check charging works
    assert sat1.battery_level_in_Ws == 500
    sim.advance_time(42, 0)
    assert sat1.battery_level_in_Ws == 542

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [10000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_power_devices(sat1, 500, 10000, 1, paseos.PowerDeviceType.SolarPanel)

    # init simulation
    sim = paseos.init_sim(sat1)

    # fast forward till eclipse
    sim.advance_time(12 * 3600, 0)

    # Check we are in eclipse
    assert is_in_eclipse(sat1, earth, sat1.local_time, plot=True)

    # Check we are fully charged
    assert sat1.battery_level_in_Ws == 10000

    # Consume 42W and check we lost corresponding SoC
    # Should not be charging currently given eclipse
    sim.advance_time(42, 1)
    assert sat1.battery_level_in_Ws == 10000 - 42


def test_RTG_charging_in_eclipse():

    # Define central body
    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [10000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_power_devices(sat1, 500, 10000, 1, paseos.PowerDeviceType.RTG)

    # init simulation
    sim = paseos.init_sim(sat1)

    # consume exactly as much power as we produce
    sim.advance_time(12 * 3600, 1)

    # Check we are in eclipse
    assert is_in_eclipse(sat1, earth, sat1.local_time, plot=True)

    # Initial power was 500m check charging works
    assert sat1.battery_level_in_Ws == 500
    sim.advance_time(42, 0)
    assert sat1.battery_level_in_Ws == 542
