"""Simple test for the operations monitor"""

import asyncio
import pytest
import pykep as pk

from test_utils import wait_for_activity
import paseos
from paseos import ActorBuilder, SpacecraftActor, load_default_cfg


# tell pytest to create an event loop and execute the tests using the event loop
@pytest.mark.asyncio
async def test_monitor():
    """Test to see if we can log while performing an activity and write to file then.
    To fully judge the outcome, have a look at the generated test file."""
    # Define central body
    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [10000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_power_devices(sat1, 500, 10000, 1)

    # init simulation
    cfg = load_default_cfg()  # loading cfg to modify defaults
    cfg.sim.dt = 0.1  # setting lower timestep to run things quickly
    cfg.sim.activity_timestep = 0.1
    cfg.io.logging_interval = 0.25  # log every 0.25 seconds
    cfg.sim.time_multiplier = 10.0  # speed up execution for convenience
    sim = paseos.init_sim(sat1, cfg)

    async def func1(args):
        await asyncio.sleep(0.5)

    async def func2(args):
        await asyncio.sleep(1.0)

    # Register an activity that draws 10 watt per second
    sim.register_activity("Activity_1", activity_function=func1, power_consumption_in_watt=2)

    sim.register_activity("Activity_2", activity_function=func2, power_consumption_in_watt=10)

    # Run the activity
    sim.perform_activity("Activity_1")
    await wait_for_activity(sim)

    sim.perform_activity("Activity_2")
    await wait_for_activity(sim)

    # Try out item function
    sim.monitor["state_of_charge"]
    sim.monitor.plot("state_of_charge")

    sim.save_status_log_csv("test.csv")
