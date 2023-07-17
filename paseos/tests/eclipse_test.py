"""Test to check the eclipse function(s)"""
import sys

sys.path.append("../..")

import pykep as pk

from test_utils import get_default_instance


def test_eclipse():
    """Get the default satellite and see if is in eclipse and getting out of it"""
    _, sat1, earth = get_default_instance()

    assert not sat1.is_in_eclipse(pk.epoch(0))
    assert sat1.is_in_eclipse(pk.epoch(0.5))


if __name__ == "__main__":
    test_eclipse()
