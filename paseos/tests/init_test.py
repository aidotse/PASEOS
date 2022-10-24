"""Tests to see if the module can be initialized and set up as planned."""

import sys

sys.path.append("../..")

from test_utils import get_default_instance


def test_init():
    sim, sat1, earth = get_default_instance()  # noqa
    cfg = sim.get_cfg()  # noqa


if __name__ == "__main__":
    test_init()
