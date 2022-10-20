"""Simple test of starting an activity"""
from test_utils import get_default_instance


def test_activity():
    """Test if performing activity consumes power as expected"""
    sim, sat1, earth = get_default_instance()

    # Initial power is 500
    assert sat1.battery_level_in_Ws == 500

    # Register an activity that draws 10 watt per second
    sim.register_activity("Testing", power_consumption_in_watt=10)

    # Run the activity for 5 seconds
    sim.perform_activity("Testing", duration_in_s=5)

    # Check power was depleted as expected
    assert sat1.battery_level_in_Ws == 450


if __name__ == "__main__":
    test_activity()
