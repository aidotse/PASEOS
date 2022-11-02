"""Simple test of starting an activity"""
from test_utils import get_default_instance

from paseos import SpacecraftActor

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
        for _ in range(10):
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
    assert test_value[0] == 10

    # Check power was depleted as expected
    # Activity should run roughly 2s
    # We charge 1W per second
    # And discharge 10W per second
    # So should be roughly 20W - 6W consumed from starting 500
    assert sat1.battery_level_in_Ws > 480 and sat1.battery_level_in_Ws < 490


def test_activity_constraints():
    """Tests if creating a constraint function to be satisfied during an activity works.
    Here we start a function that counts up until we stop charging our solar panels and then prints the value.
    """

    sim, sat1, earth = get_default_instance()
    assert sat1.battery_level_in_Ws == 500

    # Out test case is a function that increments a value, genius.
    # (needs a list so increase the actual value by reference and don't create a copy)
    test_value = [0]
    test_value2 = [-1]

    async def func(args):
        while True:
            args[0][0] += 1
            await asyncio.sleep(1.0)

    # Constraint that becomes false once the actor has charge it's battery over 510
    async def constraint(args):
        local_actor: SpacecraftActor = args[0]
        return local_actor.battery_level_in_Ws < 505

    # On termination print the value and make test_value2 the same.
    async def on_termination(args):
        print(args)
        args[1][0] = args[0][0]

    # Register an activity that draws no power per second
    sim.register_activity(
        "Testing constraints",
        activity_function=func,
        power_consumption_in_watt=0,
        on_termination_function=on_termination,
        constraint_function=constraint,
    )

    # Run the activity
    sim.perform_activity(
        "Testing constraints",
        activity_func_args=[test_value],
        constraint_func_args=[sat1],
        termination_func_args=[test_value, test_value2],
    )

    assert test_value == test_value2
    assert sat1.battery_level_in_Ws >= 505


if __name__ == "__main__":
    test_activity()
    test_activity_constraints()
