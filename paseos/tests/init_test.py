"""Tests to see if the module can be initialized and set up as planned."""

import sys

sys.path.append("../..")

from paseos import SpacecraftActor
import pykep as pk
import numpy as np

from test_utils import get_default_instance


def test_init():
    sim, sat1, earth = get_default_instance()  # noqa
    cfg = sim.get_cfg()  # noqa


def test_adding_sat():
    sim, _, earth = get_default_instance()

    sat1 = SpacecraftActor(
        "sat1", [1000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth, 1, 1, 1
    )

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

    # TODO add more checks if this was done correctly


if __name__ == "__main__":
    test_init()
    test_adding_sat()
