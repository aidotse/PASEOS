"""Tests to check line of sight computations."""
import sys

sys.path.append("../..")

from paseos import SpacecraftActor, ActorBuilder
from paseos.communication.is_in_line_of_sight import is_in_line_of_sight

import pykep as pk

from test_utils import get_default_instance


def test_los():
    """create satellites where sat1 and 2 are in sight of each other (as well as sat 1 and 3)
    but sat 2 and 3 are on opposite sides of the planet"""
    sim, sat1, earth = get_default_instance()

    sat2 = ActorBuilder.get_actor_scaffold(
        "sat2", SpacecraftActor, [10000000, 0, 0], pk.epoch(0)
    )
    ActorBuilder.set_orbit(sat2, [0, 10000000, 0], [0, 0, 8000.0], pk.epoch(0), earth)

    sat3 = ActorBuilder.get_actor_scaffold(
        "sat3", SpacecraftActor, [10000000, 0, 0], pk.epoch(0)
    )
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


if __name__ == "__main__":
    test_los()
