"""Simple test of starting an activity"""
from test_utils import get_default_instance

import asyncio


def test_activity():
    """Test if performing activity consumes power as expected"""
    sim, sat1, earth = get_default_instance()

    # Initial power is 500
    assert sat1.battery_level_in_Ws == 500

    # Out test case is a function that increments a value, genius.
    # (needs a list so increase the actual value by reference and don't create a copy)
    test_value = [0]

    async def func(args):
        for _ in range(30):
            args[0][0] += 1
            # print(args)
            await asyncio.sleep(0.2)

    # Register an activity that draws 10 watt per second
    sim.register_activity(
        "Testing", activity_function=func, power_consumption_in_watt=10
    )

    # Run the activity
    sim.perform_activity("Testing", activity_func_args=[test_value])

    # Check activity result
    assert test_value[0] == 30

    # Check power was depleted as expected
    # Activity should run roughly 6s
    # We charge 1W per second
    # And discharge 10W per second
    # So should be roughly 60W - 6W consumed from starting 500
    assert sat1.battery_level_in_Ws > 440 and sat1.battery_level_in_Ws < 450


if __name__ == "__main__":
    test_activity()
