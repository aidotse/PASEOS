"""This test checks whether power charging is performed correctly"""

from test_utils import get_default_instance


def test_power_charging():
    """Checks whether we can charge an actor"""
    sim, sat1, earth = get_default_instance()

    # Initial power is 500m check charging works
    assert sat1.battery_level_in_Ws == 500
    sim.advance_time(42, 0)
    assert sat1.battery_level_in_Ws == 542

    # TODO check charging doesn't work when in eclipse


if __name__ == "__main__":
    test_power_charging()
