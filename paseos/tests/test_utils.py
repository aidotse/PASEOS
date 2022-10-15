"""Utility for tests"""
import sys

sys.path.append("../..")

import paseos
from paseos import SpacecraftActor

import pykep as pk


def get_default_instance() -> (paseos.PASEOS, SpacecraftActor, pk.planet):
    """Sets up a instance of paseos with a satellite in orbit around Earth"""

    # Define central body
    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = SpacecraftActor(
        "sat1", [10000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth, 500, 10000, 1
    )

    # init simulation
    sim = paseos.init_sim(sat1)

    return sim, sat1, earth
