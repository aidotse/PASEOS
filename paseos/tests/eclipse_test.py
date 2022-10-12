"""Test to check the eclipse function(s)"""
import sys

sys.path.append("../..")

import paseos
from paseos.power.is_in_eclipse import is_in_eclipse
from paseos import SpacecraftActor

import pykep as pk


def test_eclipse():
    # create satellites where sat1 and 2 are in sight of each other (as well as sat 1 and 3)
    # but sat 2 and 3 are on opposite sides of the planet
    earth = pk.planet.jpl_lp("earth")
    sat1 = SpacecraftActor(
        "sat1", [10000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth, 1, 1, 1
    )

    # init simulation
    sim = paseos.init_sim(sat1)

    assert is_in_eclipse(sat1, earth, pk.epoch(0), plot=True)


if __name__ == "__main__":
    test_eclipse()
