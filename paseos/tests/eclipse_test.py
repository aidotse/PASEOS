"""Test to check the eclipse function(s)"""
import sys

sys.path.append("../..")

from paseos.power.is_in_eclipse import is_in_eclipse

import pykep as pk

from test_utils import get_default_instance


def test_eclipse():
    """Get the default satellite and see if is in eclipse and getting out of it"""
    _, sat1, earth = get_default_instance()

    assert not is_in_eclipse(sat1, earth, pk.epoch(0), plot=True)
    assert is_in_eclipse(sat1, earth, pk.epoch(0.5), plot=True)


if __name__ == "__main__":
    test_eclipse()
