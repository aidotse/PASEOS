"""Tests to see whether the attitude model works as intended"""

import numpy as np
import pykep as pk
import sys

sys.path.append("../..")
import paseos
from paseos import ActorBuilder, SpacecraftActor


def test_attitude_model():
    """Testing the attitude model with no disturbances and known angular velocity.
    One actor has orbit in Earth inertial x-y plane (equatorial) with initial velocity which rotates the actor with 180°
    in 20 steps advancing time 100 seconds (pi/ (20 * 100)).
    Another one has zero initial angular velocity.
    This test mainly checks whether the model correctly models constant angular velocity without disturbances
    """

    earth = pk.planet.jpl_lp("earth")

    # First actor constant angular acceleration
    omega = np.pi / 2000

    # Define first local actor with angular velocity
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [7000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_spacecraft_body_model(sat1, mass=100)
    ActorBuilder.set_attitude_model(
        sat1,
        actor_initial_angular_velocity=[0.0, omega, 0.0],
        actor_pointing_vector_body=[0, 0, 1],
    )

    # Define second local actor without angular velocity
    sat2 = ActorBuilder.get_actor_scaffold("sat2", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat2, [7000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_spacecraft_body_model(sat2, mass=100)
    ActorBuilder.set_attitude_model(
        sat2,
        actor_initial_angular_velocity=[0.0, 0.0, 0.0],
        actor_pointing_vector_body=[0, 0, 1],
    )

    # Check Initial values

    # sat1
    assert np.all(sat1._attitude_model._actor_pointing_vector_body == [0.0, 0.0, 1.0])
    assert np.all(sat1._attitude_model._actor_pointing_vector_eci == [-1.0, 0.0, 0.0])
    assert np.all(sat1._attitude_model._actor_attitude_in_rad == [0.0, 0.0, 0.0])
    # positive angular velocity in body y direction is negative angular velocity in Earth inertial z direction:
    assert np.all(
        sat1._attitude_model._actor_angular_velocity_eci == [0.0, 0.0, -omega]
    )

    # sat2
    assert np.all(sat2._attitude_model._actor_pointing_vector_body == [0.0, 0.0, 1.0])
    assert np.all(sat2._attitude_model._actor_pointing_vector_eci == [-1.0, 0.0, 0.0])
    assert np.all(sat2._attitude_model._actor_attitude_in_rad == [0.0, 0.0, 0.0])

    # Initialise simulation
    sim = paseos.init_sim(sat1)
    sim.add_known_actor(sat2)
    # Run simulation 20 steps
    for i in range(20):
        sim.advance_time(100, 0)

    # Testing the simulation went as intended
    # Pointing vector from sat1 must be rotated from [-1, 0, 0] to [1, 0, 0]:
    assert np.all(np.isclose(sat1.pointing_vector, np.array([1.0, 0.0, 0.0])))
    # Sat1 angular velocity in the body frame must stay constant:
    assert np.all(
        np.isclose(
            sat1._attitude_model._actor_angular_velocity,
            np.array([0.0, omega, 0.0]),
        )
    )
    # Sat1 angular velocity in the Earth inertial frame must stay constant:
    assert np.all(
        np.isclose(
            sat1.angular_velocity,
            np.array([0.0, 0.0, -omega]),
        )
    )

    # Pointing vector from sat2 must not be rotated.
    assert np.all(sat2.pointing_vector == np.array([-1.0, 0.0, 0.0]))
    # Sat2 angular velocity in the body frame must stay zero:
    assert np.all(
        sat2._attitude_model._actor_angular_velocity == np.array([0.0, 0.0, 0.0])
    )


def attitude_thermal_model_test():
    """Testing the attitude model with no disturbances and no angular velocity, and ensuring the attitude model does not
    break the thermal model (or vice versa)"""
    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [7000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_spacecraft_body_model(sat1, mass=100)
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
    ActorBuilder.set_attitude_model(sat1, actor_pointing_vector_body=[0, 0, 1])

    # Check Initial values
    assert np.all(sat1._attitude_model._actor_pointing_vector_body == [0.0, 0.0, 1.0])
    assert np.all(sat1._attitude_model._actor_attitude_in_rad == [0.0, 0.0, 0.0])
    assert sat1.temperature_in_K == 273.15

    # Initialise simulation
    sim = paseos.init_sim(sat1)

    # Run simulation 20 steps
    for i in range(21):
        vector = sat1.pointing_vector
        sim.advance_time(100, 0)

    # Testing the simulation went as intended
    assert vector[0] == -1.0
    assert sat1._attitude_model._actor_angular_velocity[1] == 0.0
    assert np.round(sat1._attitude_model._actor_attitude_in_rad[0], 3) == 3.142
    assert np.round(sat1.temperature_in_K, 3) == 278.522


def test_attitude_and_orbit():
    """This test checks both the orbit calculations, as well as the attitude.
    The input is a simple orbit, and the angular velocity if 2pi/period. This means the initial conditions should be
    the same as the conditions after one orbit"""

    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [7000000, 0, 0], [0, 5460.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_spacecraft_body_model(sat1, mass=100)
    orbit_period = 2 * np.pi * np.sqrt((6371000 + 7000000) ** 3 / 3.986004418e14)
    ActorBuilder.set_attitude_model(
        sat1,
        actor_initial_angular_velocity=[0.0, 2 * np.pi / orbit_period, 0.0],
        actor_pointing_vector_body=[0, 0, 1],
    )

    # Check Initial values
    assert np.all(sat1._attitude_model._actor_pointing_vector_body == [0.0, 0.0, 1.0])
    assert np.all(sat1._attitude_model._actor_attitude_in_rad == [0.0, 0.0, 0.0])
    vector = sat1.pointing_vector
    assert vector[0] == -1.0

    # Initialise simulation
    sim = paseos.init_sim(sat1)

    # Run simulation 10 steps
    for i in range(11):
        vector = sat1.pointing_vector
        sim.advance_time(orbit_period / 10, 0)

    # Testing the simulation went as intended
    assert sat1._attitude_model._actor_pointing_vector_body[2] == 1.0
    assert vector[0] == -1.0
