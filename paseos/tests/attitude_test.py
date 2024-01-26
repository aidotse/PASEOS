"""Tests to see whether the attitude and disturbance models work as intended"""

import numpy as np
import pykep as pk
import sys

sys.path.append("../..")
import paseos
from paseos import ActorBuilder, SpacecraftActor


def attitude_model_test():
    """Testing the attitude model with no disturbances and known angular velocity.
    This test mainly checks that the attitude calculations are correct, but it doesn't check the reference
    frame transformations"""
    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [7000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_geometric_model(sat1, mass=100)
    ActorBuilder.set_attitude_model(sat1,
                                    actor_initial_angular_velocity=[0.0, np.pi/2000, 0.0],
                                    actor_pointing_vector_body=[0, 0, 1])
    ActorBuilder.set_disturbances(sat1)

    # Check Initial values
    assert np.all(sat1._attitude_model._actor_pointing_vector_body == [0.0, 0.0, 1.0])
    assert np.all(sat1._attitude_model._actor_attitude_in_rad == [0.0, 0.0, 0.0])

    # Initialise simulation
    sim = paseos.init_sim(sat1)

    # Run simulation 20 steps
    for i in range(21):
        vector = sat1.pointing_vector()
        sim.advance_time(100, 0)

    # Testing the simulation went as intended
    assert vector[0] == 1.0
    assert np.round(sat1._attitude_model._actor_angular_velocity[1],5) == 0.00157

def attitude_thermal_model_test():
    """Testing the attitude model with no disturbances and no angular velocity, and ensuring the attitude model doesn't
    break the thermal model (or vice versa)"""
    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [7000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_geometric_model(sat1, mass=100)
    ActorBuilder.set_thermal_model(
        actor=sat1,
        actor_mass=sat1.mass,
        actor_initial_temperature_in_K=273.15,
        actor_sun_absorptance=1.0,
        actor_infrared_absorptance=1.0,
        actor_sun_facing_area=1.0,
        actor_central_body_facing_area=1.0,
        actor_emissive_area=1.0,
        actor_thermal_capacity=1000,
    )
    ActorBuilder.set_attitude_model(sat1,
                                    actor_pointing_vector_body=[0, 0, 1])

    # Check Initial values
    assert np.all(sat1._attitude_model._actor_pointing_vector_body == [0.0, 0.0, 1.0])
    assert np.all(sat1._attitude_model._actor_attitude_in_rad == [0.0, 0.0, 0.0])
    assert sat1.temperature_in_K == 273.15

    # Initialise simulation
    sim = paseos.init_sim(sat1)

    # Run simulation 20 steps
    for i in range(21):
        vector = sat1.pointing_vector()
        sim.advance_time(100, 0)

    # Testing the simulation went as intended
    assert vector[0] == -1.0
    assert sat1._attitude_model._actor_angular_velocity[1] == 0.0
    assert np.round(sat1._attitude_model._actor_attitude_in_rad[0], 3) == 3.142
    assert np.round(sat1.temperature_in_K,3) == 278.522

def attitude_and_orbit_test():
    """This test checks both the orbit calculations, as well as the attitude.
    The input is a simple orbit, and the angular velocity if 2pi/period. This means the initial conditions should be
    the same as the conditions after one orbit"""

    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [7000000, 0, 0], [0, 5460.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_geometric_model(sat1, mass=100)
    orbit_period = 2 * np.pi * np.sqrt((6371000+7000000) ** 3 / 3.986004418e14)
    ActorBuilder.set_attitude_model(sat1,
                                    actor_initial_angular_velocity=[0.0, 2*np.pi / orbit_period, 0.0],
                                    actor_pointing_vector_body=[0, 0, 1])
    ActorBuilder.set_disturbances(sat1)

    # Check Initial values
    assert np.all(sat1._attitude_model._actor_pointing_vector_body == [0.0, 0.0, 1.0])
    assert np.all(sat1._attitude_model._actor_attitude_in_rad == [0.0, 0.0, 0.0])
    vector = sat1.pointing_vector()
    assert vector[0] == -1.0

    # Initialise simulation
    sim = paseos.init_sim(sat1)

    # Run simulation 10 steps
    for i in range(11):
        vector = sat1.pointing_vector()
        sim.advance_time(orbit_period/10, 0)

    # Testing the simulation went as intended
    assert sat1._attitude_model._actor_pointing_vector_body[2] == 1.0
    assert vector[0] == -1.0
