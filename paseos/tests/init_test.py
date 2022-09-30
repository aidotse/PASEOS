"""Tests to see if the module can be initialized and set up as planned."""

import sys

sys.path.append("../..")


def test_init():
    import paseos

    sim = paseos.init_sim()
    cfg = sim.get_cfg()  # noqa


if __name__ == "__main__":
    test_init()
