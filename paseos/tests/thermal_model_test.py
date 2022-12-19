"""Simple test of the thermal model to see if temperatures evolve as expected"""
import pykep as pk

import paseos
from paseos import SpacecraftActor, ActorBuilder, load_default_cfg
import asyncio
import pytest


async def wait_for_activity(sim):
    while sim._is_running_activity is True:
        await asyncio.sleep(0.1)


# tell pytest to create an event loop and execute the tests using the event loop
@pytest.mark.asyncio
async def test_thermal():
    """Test if performing activity changes temperature as expected"""

    # Define central body
    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [10000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_power_devices(sat1, 500, 10000, 1)
    ActorBuilder.set_thermal_model(
        actor=sat1,
        actor_mass=50.0,
        actor_initial_temperature_in_K=273.15,
        actor_sun_absorptance=1.0,
        actor_infrared_absorptance=1.0,
        actor_sun_facing_area=1.0,
        actor_central_body_facing_area=1.0,
        actor_emissive_area=1.0,
        actor_thermal_capacity=1000,
    )

    # init simulation
    cfg = load_default_cfg()  # loading cfg to modify defaults
    cfg.sim.dt = 0.1  # setting lower timestep to run things quickly
    cfg.sim.activity_timestep = 0.1
    cfg.io.logging_interval = 0.25  # log every 0.25 seconds
    cfg.sim.time_multiplier = 50  # speed up execution for convenience
    sim = paseos.init_sim(sat1, cfg)

    # Initial temperature is 0C / 273.15K
    assert sat1.temperature_in_K == 273.15

    async def func(args):
        await asyncio.sleep(3.0)

    # Register an activity that draws 10 watt per second
    sim.register_activity(
        "Activity_1", activity_function=func, power_consumption_in_watt=10
    )

    # Run the activity
    sim.perform_activity("Activity_1")
    await wait_for_activity(sim)
    raise (1)


if __name__ == "__main__":
    test_thermal()
