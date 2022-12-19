"""Tests to check line of sight computations."""
import sys

sys.path.append("../..")

from paseos import SpacecraftActor, ActorBuilder, GroundstationActor
from paseos.communication.is_in_line_of_sight import is_in_line_of_sight

import pykep as pk

from test_utils import get_default_instance


def test_los_between_sats():
    """create satellites where sat1 and 2 are in sight of each other (as well as sat 1 and 3)
    but sat 2 and 3 are on opposite sides of the planet"""
    _, sat1, earth = get_default_instance()

    sat2 = ActorBuilder.get_actor_scaffold("sat2", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat2, [0, 10000000, 0], [0, 0, 8000.0], pk.epoch(0), earth)

    sat3 = ActorBuilder.get_actor_scaffold("sat3", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat3, [0, -10000000, 0], [0, 0, -8000.0], pk.epoch(0), earth)

    # check that LOS is correct
    assert sat1.is_in_line_of_sight(sat2, pk.epoch(0))
    assert sat1.is_in_line_of_sight(sat3, pk.epoch(0))
    assert not sat2.is_in_line_of_sight(sat3, pk.epoch(0))

    # also check the backend function directly
    # also check reverse case (should be same)
    assert is_in_line_of_sight(sat1, sat2, pk.epoch(0))
    assert is_in_line_of_sight(sat2, sat1, pk.epoch(0))
    assert is_in_line_of_sight(sat1, sat3, pk.epoch(0))
    assert is_in_line_of_sight(sat3, sat1, pk.epoch(0))
    assert not is_in_line_of_sight(sat2, sat3, pk.epoch(0))
    assert not is_in_line_of_sight(sat3, sat2, pk.epoch(0))


def test_los_sat_to_ground_station_equatorial():
    """Equatorial ground station and orbit"""
    t = pk.epoch(0)
    ground_station = GroundstationActor("gs", t)

    # Put GS at lat long 0 , 0 with elevation 0m
    ActorBuilder.set_ground_station_location(ground_station, 0, 0, 0)

    _, sat1, earth = get_default_instance()

    # Put the sat over the equator
    ActorBuilder.set_orbit(sat1, [10000000, 0, 0], [0, 0, 0], t, earth)

    # Not in vision initially.
    assert not ground_station.is_in_line_of_sight(sat1, t, 30.0)

    # But after 0.7 days
    assert ground_station.is_in_line_of_sight(sat1, pk.epoch(0.7), 65.0)

    # Put the sat over the equator, higher up
    ActorBuilder.set_orbit(sat1, [100000000, 0, 0], [0, 0, 0], t, earth)

    # Not in vision initially.
    assert not ground_station.is_in_line_of_sight(sat1, t, 30.0)

    # But after 0.7 days
    assert ground_station.is_in_line_of_sight(sat1, pk.epoch(0.7), 80.0)


def test_los_sat_to_ground_station_polar():
    """Satellite above the north pole, ground station on the equator and vice versa"""
    t = pk.epoch(0)
    ground_station = GroundstationActor("gs", t)

    # Put GS at lat long 0 , 0 with elevation 0m
    ActorBuilder.set_ground_station_location(ground_station, 0, 0, 0)

    _, sat1, earth = get_default_instance()

    # Put the sat over the north pole
    ActorBuilder.set_orbit(sat1, [0, 0, 10000000], [0, 0, 0], t, earth)

    # Not in vision at this height
    assert not ground_station.is_in_line_of_sight(sat1, t, 0.1)

    # Even after 0.7 days
    assert not ground_station.is_in_line_of_sight(sat1, pk.epoch(0.7), 0.1)

    # Put GS at Norht Pole lat 90 long 0 , 0 with elevation 0m
    ActorBuilder.set_ground_station_location(ground_station, 90, 0, 0)

    # Always vision now (almost 90deg)
    assert ground_station.is_in_line_of_sight(sat1, t, 89.0)

    # Even after 0.7 days
    assert ground_station.is_in_line_of_sight(sat1, pk.epoch(0.7), 89.0)

    # Put the sat over the equator, GS remains at north pole
    ActorBuilder.set_orbit(sat1, [0, 10000000, 0], [0, 0, 0], t, earth)

    # Never vision now
    assert not ground_station.is_in_line_of_sight(sat1, t, 0.1)

    # Even after 0.7 days
    assert not ground_station.is_in_line_of_sight(sat1, pk.epoch(0.7), 0.1)


def test_los_sat_to_ground_station_elevation():
    """Testing how elevation of ground station affects angle"""
    t = pk.epoch(0)
    ground_station = GroundstationActor("gs", t)

    # Start with GS at lat long 10 / 30 , 0 with elevation 0m
    ActorBuilder.set_ground_station_location(ground_station, 10, 30, 0)

    _, sat1, earth = get_default_instance()

    # Put the sat over the equator
    ActorBuilder.set_orbit(sat1, [100000000, 0, 0], [0, 0, 0], t, earth)

    # Not in vision at this height initially
    assert not ground_station.is_in_line_of_sight(sat1, t, 0.1)

    # But after 0.6 days at angle > 68.2
    assert ground_station.is_in_line_of_sight(sat1, pk.epoch(0.6), 68.2)

    # Start with GS at lat long 10 / 30 , 0 with elevation 10000m
    ActorBuilder.set_ground_station_location(ground_station, 10, 30, 10000)

    # Not in vision at this height initially
    assert not ground_station.is_in_line_of_sight(sat1, t, 0.1)

    # Still not at this height!
    assert not ground_station.is_in_line_of_sight(sat1, pk.epoch(0.6), 68.2)


if __name__ == "__main__":
    test_los_between_sats()
    test_los_sat_to_ground_station_equatorial()
    test_los_sat_to_ground_station_polar()
    test_los_sat_to_ground_station_elevation()
