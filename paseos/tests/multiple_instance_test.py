"""This test runs the power charging test on two devices"""

from test_utils import get_default_instance


def test_multiple_instances():
    """Checks whether we can charge an actor"""
    sim, sat1, _ = get_default_instance()
    sim2, sat2, _ = get_default_instance()

    # Initial power is 500m check charging works
    assert sat1.battery_level_in_Ws == 500
    assert sat2.battery_level_in_Ws == 500
    sim.advance_time(42)
    assert sat1.battery_level_in_Ws == 542
    assert sat2.battery_level_in_Ws == 500

    sim2.advance_time(42)
    assert sat1.battery_level_in_Ws == 542
    assert sat2.battery_level_in_Ws == 542
