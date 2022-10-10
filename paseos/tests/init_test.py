"""Tests to see if the module can be initialized and set up as planned."""

import sys

sys.path.append("../..")

import paseos
from paseos import SpacecraftActor
import pykep as pk
import numpy as np


def test_init():
    sim = paseos.init_sim()
    cfg = sim.get_cfg()  # noqa
    print(cfg)


def test_adding_sat():
    earth = pk.planet.jpl_lp("earth")
    actor = SpacecraftActor("sat1", [1000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    sim = paseos.init_sim()
    sim.add_actor(actor)

    # check initial positions
    # r - position vector, v - velocity vector
    r, v = actor.get_position_velocity(pk.epoch(0))
    assert np.isclose(r[0], 1000000)
    assert np.isclose(r[1], 0)
    assert np.isclose(r[2], 0)
    assert np.isclose(v[0], 0)
    assert np.isclose(v[1], 8000.0)
    assert np.isclose(v[2], 0)

    # check positions one second later
    r, v = actor.get_position_velocity(pk.epoch(1 * pk.SEC2DAY))
    assert np.isclose(r[0], 999800.6897266058)
    assert np.isclose(r[1], 7999.468463301808)
    assert np.isclose(r[2], 0.0)
    assert np.isclose(v[0], -398.64065398803876)
    assert np.isclose(v[1], 7998.405250997527)
    assert np.isclose(v[2], 0.0)

    # TODO add more checks if this was done correctly


if __name__ == "__main__":
    test_init()
    test_adding_sat()
