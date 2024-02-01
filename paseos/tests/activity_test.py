"""Simple test of starting an activity"""
from test_utils import get_default_instance, wait_for_activity

from paseos import SpacecraftActor
import asyncio
import pytest

# Below test can be used to check what happens when you formulate an invalid constraint function.
# It is temporarily commented out as it doesn't really check right now because I could not figure
# out a way to get an exception raised from the async code.
# @pytest.mark.asyncio
# async def test_faulty_constraint_function():
#     """Check whether specifying a wrong constraint function leads to an error"""

#     sim, _, _ = get_default_instance()

#     # A pointless activity
#     async def func(args):
#         await asyncio.sleep(1.5)

#     # A constraint function that fails to return True or False
#     async def constraint(args):
#         pass

#     # Register an activity that draws 10 watt per second
#     sim.register_activity(
#         "Testing",
#         activity_function=func,
#         constraint_function=constraint,
#         power_consumption_in_watt=10,
#     )

#     # Run the activity
#     sim.perform_activity("Testing")
#     await wait_for_activity(sim)


# tell pytest to create an event loop and execute the tests using the event loop
@pytest.mark.asyncio
async def test_activity():
    """Test if performing activity consumes power as expected"""
    sim, sat1, _ = get_default_instance()

    # Initial power is 500
    assert sat1.battery_level_in_Ws == 500

    # Out test case is a function that increments a value, genius.
    # (needs a list to increase the actual value by reference and not create a copy)
    test_val = [0]

    async def func(args):
        for _ in range(10):
            args[0][0] += 1
            await asyncio.sleep(0.2)

    # Register an activity that draws 10 watt per second
    sim.register_activity(
        "Testing", activity_function=func, power_consumption_in_watt=10
    )

    # Run the activity
    sim.perform_activity("Testing", activity_func_args=[test_val])
    await wait_for_activity(sim)

    # Check activity result
    assert test_val[0] == 10

    # Check power was depleted as expected
    # Activity should run roughly 2s
    # We charge 1W per second
    # And discharge 10W per second
    # So should be roughly 20W - 6W consumed from starting 500
    assert sat1.battery_level_in_Ws > 475 and sat1.battery_level_in_Ws < 490

    # test removing the activity
    assert "Testing" in sim._activity_manager._activities.keys()
    sim.remove_activity("Testing")
    assert "Testing" not in sim._activity_manager._activities.keys()


@pytest.mark.asyncio
async def test_running_two_activities():
    """This test ensures that you cannot run two activities at the same time."""
    sim, _, _ = get_default_instance()

    # Declare two activities, one calls the other
    test_value = [0]

    async def act1(args):
        args[0][0] = 42  # this gets executed
        sim.perform_activity("act2")
        await asyncio.sleep(0.1)

    async def act2(args):
        args[0][0] = -1  # this won't
        await asyncio.sleep(0.1)

    # Register both activities
    sim.register_activity("act1", activity_function=act1, power_consumption_in_watt=10)
    sim.register_activity("act2", activity_function=act2, power_consumption_in_watt=10)

    # try running it
    sim.perform_activity("act1", activity_func_args=[test_value])
    await wait_for_activity(sim)

    # Value should be 42 as first activity is started but then an error occurs trying the second
    assert test_value[0] == 42


@pytest.mark.asyncio
async def test_activity_constraints():
    """Tests if creating a constraint function to be satisfied during an activity works.
    Here we start a function that counts up until we stop charging our solar panels and then prints the value.
    """

    sim, sat1, _ = get_default_instance()
    assert sat1.battery_level_in_Ws == 500

    # Out test case is a function that increments a value, genius.
    # (needs a list so increase the actual value by reference and don't create a copy)
    test_value = [0]
    test_value2 = [-1]

    async def func(args):
        while True:
            args[0][0] += 1
            await asyncio.sleep(1.0)

    # Constraint that becomes false once the actor has charged it's battery over 510
    async def constraint(args):
        local_actor: SpacecraftActor = args[0]
        return local_actor.battery_level_in_Ws < 505

    # On termination print the value and make test_value2 the same.
    async def on_termination(args):
        # print(args)
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
    await wait_for_activity(sim)

    assert test_value == test_value2
    assert sat1.battery_level_in_Ws >= 505
