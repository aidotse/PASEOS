"""Simple test of modifying rate of time passing"""

import asyncio
import pytest
import pykep as pk

from test_utils import wait_for_activity
import paseos
from paseos import ActorBuilder, SpacecraftActor, load_default_cfg


# tell pytest to create an event loop and execute the tests using the event loop
@pytest.mark.asyncio
async def test_activity():
    """Test to see if twice as much power is consumed given the higher than real-time multiplier"""
    # Define central body
    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [10000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_power_devices(sat1, 500, 10000, 1)
    # init simulation

    cfg = load_default_cfg()  # loading cfg to modify defaults
    cfg.sim.time_multiplier = 5.0
    sim = paseos.init_sim(sat1, cfg)

    # Initial power is 500
    assert sat1.battery_level_in_Ws == 500

    # Out test case is a function that increments a value, genius.
    # (needs a list to increase the actual value by reference and not create a copy)
    test_val = [0]

    async def func(args):
        for _ in range(5):
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
    assert test_val[0] == 5

    # Check power was depleted as expected
    # Activity should run roughly 1s
    # We charge 1W per second
    # 1s real time equals 5s simulation
    # And discharge 10W per second
    # So should be roughly 50W - 5W consumed from starting 500
    assert sat1.battery_level_in_Ws > 350 and sat1.battery_level_in_Ws <= 456
