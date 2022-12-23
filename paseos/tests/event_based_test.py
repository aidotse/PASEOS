"""Simple test for the operations monitor"""

import numpy as np
import pykep as pk

import paseos
from paseos import ActorBuilder, SpacecraftActor, load_default_cfg


async def test_event_based_mode():
    """Test to see if we use PASEOS with just the "advance_time" function instead of async activity stuff"""
    # Define central body
    earth = pk.planet.jpl_lp("earth")

    # Define some satellite with a few physical models
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [10000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_power_devices(sat1, 500, 1000, 1)
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

    # Check initial condition
    assert sat1.temperature_in_K == 273.15
    assert sat1.battery_level_in_Ws == 500
    assert np.isclose(sat1.state_of_charge, 0.5)

    def constraint_func():
        # Abort when sat is at 10% battery
        print(sat1.state_of_charge)
        return sat1.state_of_charge > 0.1

    # init simulation
    cfg = load_default_cfg()  # loading cfg to modify defaults
    cfg.sim.dt = 0.1  # setting higher timestep to run things quickly
    cfg.sim.activity_timestep = 1.0  # frequency of constraint func
    sim = paseos.init_sim(sat1, cfg)

    # Advance for long time, will interrupt much sooner due to power outage
    sim.advance_time(3600, 10, constraint_function=constraint_func)

    assert sat1.temperature_in_K > 274  # should be a little hotter

    # Power should have gone to roughly 10%
    assert sat1.battery_level_in_Ws > 90 and sat1.battery_level_in_Ws < 100
