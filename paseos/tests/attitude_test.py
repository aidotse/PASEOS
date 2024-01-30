"""Tests to see whether the attitude and disturbance models work as intended"""
import numpy as np
import pykep as pk
import sys

sys.path.append("../..")
import paseos
from paseos import ActorBuilder, SpacecraftActor, load_default_cfg


def gravity_disturbance_cube_test():
    """This test checks whether a 3-axis symmetric, uniform body (a cube with constant density, and cg at origin)
    creates no angular acceleration/velocity due to gravity"""
    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [7000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_geometric_model(sat1, mass=100)
    ActorBuilder.set_attitude_model(sat1)
    ActorBuilder.set_disturbances(sat1, gravitational=True)

    # init simulation
    sim = paseos.init_sim(sat1)

    # Check initial conditions
    assert np.all(sat1._attitude_model._actor_angular_velocity == 0.0)

    # run simulation for 1 period
    orbital_period = 2 * np.pi * np.sqrt((6371000 + 7000000) ** 3 / 3.986004418e14)
    sim.advance_time(orbital_period, 0)
    nadir = sat1._attitude_model.nadir_vector()

    # check conditions after 1 orbit
    assert np.all(sat1._attitude_model._actor_angular_acceleration == 0.0)

def gravity_disturbance_pole_test():
    """This test checks whether a 2-axis symmetric, uniform body (a pole (10x1x1) with constant density, and cg at
    origin) stabilises in orbit due to gravitational acceleration
    It additionally checks the implementation of custom meshes of the geometric model"""

    vertices = [
                [-5, -0.5, -0.5],
                [-5, -0.5, 0.5],
        [-5, 0.5, -0.5],
        [-5, 0.5, 0.5],
        [5, -0.5, -0.5],
        [5, -0.5, 0.5],
        [5, 0.5, -0.5],
        [5, 0.5, 0.5],
    ]
    faces = [
        [0, 1, 3],
        [0, 3, 2],
        [0, 2, 6],
        [0, 6, 4],
        [1, 5, 3],
        [3, 5, 7],
        [2, 3, 7],
        [2, 7, 6],
        [4, 6, 7],
        [4, 7, 5],
        [0, 4, 1],
        [1, 4, 5],
    ]

    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [7000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_geometric_model(sat1, mass=100, vertices=vertices, faces=faces)
    orbital_period = 2 * np.pi * np.sqrt((6371000 + 7000000) ** 3 / 3.986004418e14)
    ActorBuilder.set_attitude_model(sat1)#, actor_initial_angular_velocity=[0,2*np.pi/orbital_period,0])
    ActorBuilder.set_disturbances(sat1, gravitational=True)

    # init simulation
    cfg = load_default_cfg()  # loading cfg to modify defaults
    cfg.sim.dt = 100.0  # setting higher timestep to run things quickly
    sim = paseos.init_sim(sat1, cfg)


    # Check initial conditions
    assert np.all(sat1._attitude_model._actor_attitude_in_rad == 0.0)

    # run simulation for 1 period
    for i in range(11):
        sim.advance_time(orbital_period*0.1, 0)

    # check conditions after 0.1 orbit, satellite should have acceleration around y-axis to align pole towards earth
    assert np.round(sat1._attitude_model._actor_angular_acceleration[0],10) == 0.0
    assert not np.round(sat1._attitude_model._actor_angular_acceleration[1],10) == 0.0

def attitude_model_test():
    """Testing the attitude model with no disturbances and known angular velocity.
    One actor has orbit in Earth inertial x-y plane (equatorial) with initial velocity which rotates the actor with 180°
    in 20 steps advancing time 100 seconds (pi/ (20 * 100)).
    Another one has zero initial angular velocity.
    This test mainly checks whether the model correctly models constant angular velocity without disturbances
    """

    earth = pk.planet.jpl_lp("earth")

    # First actor constant angular acceleration
    omega = np.pi/2000

    # Define first local actor with angular velocity
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [7000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_geometric_model(sat1, mass=100)
    ActorBuilder.set_attitude_model(
        sat1,
        actor_initial_angular_velocity=[0.0, omega, 0.0],
        actor_pointing_vector_body=[0, 0, 1],
    )

    # Define second local actor without angular velocity
    sat2 = ActorBuilder.get_actor_scaffold("sat2", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat2, [7000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_geometric_model(sat2, mass=100)
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
    assert np.all(sat1._attitude_model._actor_angular_velocity_eci == [0.0, 0.0, -omega])

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
    assert np.all(np.isclose(sat1.pointing_vector(), np.array([1.0, 0.0, 0.0])))
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
            sat1.angular_velocity(),
            np.array([0.0, 0.0, -omega]),
        )
    )

    # Pointing vector from sat2 must not be rotated.
    assert np.all(sat2.pointing_vector() == np.array([-1.0, 0.0, 0.0]))
    # Sat2 angular velocity in the body frame must stay zero:
    assert np.all(sat2._attitude_model._actor_angular_velocity == np.array([0.0, 0.0, 0.0]))


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
    ActorBuilder.set_attitude_model(sat1, actor_pointing_vector_body=[0, 0, 1])

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
    assert np.round(sat1.temperature_in_K, 3) == 278.522


def attitude_and_orbit_test():
    """This test checks both the orbit calculations, as well as the attitude.
    The input is a simple orbit, and the angular velocity if 2pi/period. This means the initial conditions should be
    the same as the conditions after one orbit"""

    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [7000000, 0, 0], [0, 5460.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_geometric_model(sat1, mass=100)
    orbit_period = 2 * np.pi * np.sqrt((6371000 + 7000000) ** 3 / 3.986004418e14)
    ActorBuilder.set_attitude_model(
        sat1,
        actor_initial_angular_velocity=[0.0, 2 * np.pi / orbit_period, 0.0],
        actor_pointing_vector_body=[0, 0, 1],
    )
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
        sim.advance_time(orbit_period / 10, 0)

    # Testing the simulation went as intended
    assert sat1._attitude_model._actor_pointing_vector_body[2] == 1.0
    assert vector[0] == -1.0