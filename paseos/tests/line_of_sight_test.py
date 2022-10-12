"""Tests to check line of sight computations."""
import sys

sys.path.append("../..")

import paseos
from paseos import SpacecraftActor

import pykep as pk


def test_los():
    """create satellites where sat1 and 2 are in sight of each other (as well as sat 1 and 3)
    but sat 2 and 3 are on opposite sides of the planet"""

    # Define central body
    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = SpacecraftActor(
        "sat1", [10000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth, 1, 1, 1
    )

    # init simulation
    sim = paseos.init_sim(sat1)

    sat2 = SpacecraftActor(
        "sat2", [0, 10000000, 0], [0, 0, 8000.0], pk.epoch(0), earth, 1, 1, 1
    )
    sim.add_known_actor(sat2)
    sat3 = SpacecraftActor(
        "sat3", [0, -10000000, 0], [0, 0, -8000.0], pk.epoch(0), earth, 1, 1, 1
    )
    sim.add_known_actor(sat3)

    # check that LOS is correct
    assert sat1.is_in_line_of_sight(sat2, pk.epoch(0))
    assert sat1.is_in_line_of_sight(sat3, pk.epoch(0))
    assert not sat2.is_in_line_of_sight(sat3, pk.epoch(0))


if __name__ == "__main__":
    test_los()
