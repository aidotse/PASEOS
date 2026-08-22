"""Regression tests for the advance_time re-entrancy guard.

These cover the failure modes fixed alongside the uv/Python 3.8 CI migration:
the guard used to be set before argument validation and only cleared on the
normal return, so a zero-length interval or an exception mid-advance_time left
it stuck True and poisoned every later call (deadlocking wait_for_activity).
"""

import sys

sys.path.append("../..")

import pytest
from test_utils import get_default_instance


def test_advance_time_zero_interval_is_noop():
    """Advancing by zero returns 0.0 and never engages the guard."""
    sim, _, _ = get_default_instance()

    assert sim.advance_time(0, 0) == 0.0
    assert sim._is_advancing_time is False

    # A normal advancement still works right after a zero-length call.
    assert sim.advance_time(10, 0) == 0
    assert sim._is_advancing_time is False


def test_advance_time_releases_guard_on_exception():
    """An exception mid-advance_time must still release the guard.

    Previously the guard leaked True and the next call failed the
    'advance_time is already running' assertion, deadlocking the simulation.
    """
    sim, _, _ = get_default_instance()

    # A constraint function returning None raises inside advance_time (after the
    # guard is set), which must be cleaned up by the finally block.
    with pytest.raises(AssertionError):
        sim.advance_time(10, 0, constraint_function=lambda: None)
    assert sim._is_advancing_time is False

    # The guard was not left poisoned, so a subsequent call still succeeds.
    assert sim.advance_time(10, 0) == 0
    assert sim._is_advancing_time is False
