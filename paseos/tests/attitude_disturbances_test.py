"""Tests to see whether the attitude disturbance models work as intended"""

import numpy as np
import pykep as pk
import sys

sys.path.append("../..")
import paseos
from paseos import ActorBuilder, SpacecraftActor
from paseos.utils.reference_frame_transfer import eci_to_rpy, rpy_to_body
from paseos.utils.load_default_cfg import load_default_cfg


def test_gravity_disturbance_cube():
    """This test checks whether a 3-axis symmetric, uniform body (a cube with constant density, and cg at origin)
    creates no angular acceleration/velocity due to gravity. The spacecraft is initially positioned with the z-axis
    aligned with the nadir vector."""
    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [7000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_spacecraft_body_model(sat1, mass=100)
    ActorBuilder.set_attitude_model(sat1)
    ActorBuilder.set_attitude_disturbances(sat1, gravitational=True)

    # init simulation
    sim = paseos.init_sim(sat1)

    # Check initial conditions
    assert np.all(sat1._attitude_model._actor_angular_velocity == 0.0)

    # run simulation for 1 period
    orbital_period = 2 * np.pi * np.sqrt((6371000 + 7000000) ** 3 / 3.986004418e14)
    sim.advance_time(orbital_period, 0)

    # check conditions after 1 orbit
    assert np.all(np.round(sat1._attitude_model._actor_angular_acceleration, 10) == 0.0)


def test_gravity_disturbance_pole():
    """This test checks whether a 2-axis symmetric, uniform body (a pole (10x1x1) with constant density, and cg at
    origin) stabilises in orbit due to gravitational acceleration. The attitude at time zero is the z-axis pointing
    towards earth. Hence, the accelerations should occur only in the y-axis.
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
    ActorBuilder.set_spacecraft_body_model(sat1, mass=100, vertices=vertices, faces=faces)
    orbital_period = 2 * np.pi * np.sqrt((6371000 + 7000000) ** 3 / 3.986004418e14)
    ActorBuilder.set_attitude_model(
        sat1
    )  # , actor_initial_angular_velocity=[0,2*np.pi/orbital_period,0])
    ActorBuilder.set_attitude_disturbances(sat1, gravitational=True)

    # init simulation
    cfg = load_default_cfg()  # loading cfg to modify defaults
    cfg.sim.dt = 100.0  # setting higher timestep to run things quickly
    sim = paseos.init_sim(sat1, cfg)

    # Check initial conditions
    assert np.all(sat1._attitude_model._actor_attitude_in_rad == 0.0)

    # run simulation for 1 period
    for i in range(11):
        sim.advance_time(orbital_period * 0.1, 0)

    # check conditions after 0.1 orbit, satellite should have acceleration around y-axis to align pole towards earth
    assert np.round(sat1._attitude_model._actor_angular_acceleration[0], 10) == 0.0
    assert not np.round(sat1._attitude_model._actor_angular_acceleration[1], 10) == 0.0


def test_magnetic_disturbance():
    """Tests the magnetic disturbance torques applied in the attitude model.
    Put two spacecraft actors in a geostationary orbit (disregarding the relative magnetic field rotation of the Earth).
    Both actor's own magnetic dipole moment aligned with the local magnetic flux density vector of the Earth
    magnetic field. One is non-magnetic and is expected to have a fixed attitude in the Earth inertial frame.
    The other (magnetic) actor should stay aligned with the Earth magnetic field.
    """

    def flux_density_vector(actor, frame="eci"):
        """Function to calculate the local magnetic field flux density vector (B) at the actor's location.
        B vector is calculated multiple times. Use of this function for code clarity.

        Args:
            actor (SpacecraftActor): Spacecraft actor
            frame (string): B expressed in which frame (actor body frame or Earth-centered inertial frame)

        Returns: B vector (np.ndarray)
        """
        # get Earth B vector at specific timestep
        # Earth magnetic dipole moment:
        m_earth = actor.central_body.magnetic_dipole_moment(actor.local_time)

        # parameters to calculate local B vector:
        actor_position = np.array(actor.get_position(actor.local_time))
        r = np.linalg.norm(actor_position)
        r_hat = actor_position / r

        # local B vector:
        B = 1e-7 * (3 * np.dot(m_earth, r_hat) * r_hat - m_earth) / (r**3)
        if frame == "eci":
            # return B vector in ECI frame
            return B
        elif frame == "body":
            # transform B vector to the actor body frame and return
            actor_velocity = np.array(actor.get_position_velocity(actor.local_time)[1])
            actor_attitude = np.array(actor.attitude_in_rad)
            return rpy_to_body(eci_to_rpy(B, actor_position, actor_velocity), actor_attitude)

    # Define central body
    earth = pk.planet.jpl_lp("earth")

    # Define spacecraft actors
    # magnetic:
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    # non-magnetic:
    sat2 = ActorBuilder.get_actor_scaffold("sat2", SpacecraftActor, pk.epoch(0))

    # Geostationary orbital parameters:
    r = 6371000 + 35786000  # radius [km]
    v = 3074.66  # velocity [m/s]

    # To have a more symmetric case, let the actors be on same longitude as Earth magnetic dipole vector
    longitude = -71.6 * np.pi / 180

    # Set orbits:
    ActorBuilder.set_orbit(
        sat1,
        position=[
            r * np.cos(np.pi / 2 + longitude),
            r * np.sin(np.pi / 2 + longitude),
            0,
        ],
        velocity=[
            -v * np.sin(np.pi / 2 + longitude),
            v * np.cos(np.pi / 2 + longitude),
            0,
        ],
        epoch=pk.epoch(0),
        central_body=earth,
    )
    ActorBuilder.set_orbit(
        sat2,
        position=[
            r * np.cos(np.pi / 2 + longitude),
            r * np.sin(np.pi / 2 + longitude),
            0,
        ],
        velocity=[
            -v * np.sin(np.pi / 2 + longitude),
            v * np.cos(np.pi / 2 + longitude),
            0,
        ],
        epoch=pk.epoch(0),
        central_body=earth,
    )

    # Set geometric model
    ActorBuilder.set_spacecraft_body_model(sat1, mass=100)
    ActorBuilder.set_spacecraft_body_model(sat2, mass=100)

    # Now, align the body magnetic dipole with the local Earth magnetic flux density vector
    # Earth magnetic flux density vector at start position is approximately:
    B0 = np.array([3.18159529e-09, -1.02244882e-07, 3.72362170e-08])

    B_direction = B0 / np.linalg.norm(B0)

    # Define a very large dipole moment for magnetic actor to compensate for the low magnetic field at GEO orbit
    m_body = 500  # Am²
    actor_dipole = np.ndarray.tolist(B_direction * m_body)
    initial_pointing_vector_body = np.ndarray.tolist(B_direction)

    # Set attitude models
    ActorBuilder.set_attitude_model(
        sat1,
        actor_initial_angular_velocity=[0.0, 0.0, 0.0],
        actor_pointing_vector_body=initial_pointing_vector_body,
        actor_initial_attitude_in_rad=[0.0, 0.0, 0.0],
        actor_residual_magnetic_field_body=actor_dipole,  # magnetic
    )

    ActorBuilder.set_attitude_model(
        sat2,
        actor_initial_angular_velocity=[0.0, 0.0, 0.0],
        actor_pointing_vector_body=initial_pointing_vector_body,
        actor_initial_attitude_in_rad=[0.0, 0.0, 0.0],
        actor_residual_magnetic_field_body=[0.0, 0.0, 0.0],  # non-magnetic
    )

    # Disturbances:
    ActorBuilder.set_attitude_disturbances(sat1, magnetic=True)
    ActorBuilder.set_attitude_disturbances(sat2, magnetic=True)

    # Initial pointing vector in Earth inertial frame
    initial_pointing_vector_eci = np.array(sat1.pointing_vector)
    # Check if pointing vectors in Earth inertial frame are equal
    assert np.all(sat1.pointing_vector == sat2.pointing_vector)

    # Start simulation
    sim = paseos.init_sim(sat1)
    sim.add_known_actor(sat2)

    # Check if B0, used to define the actors' magnetic field orientations is the initial B vector orientation in sim.
    assert np.all(np.isclose(B0, flux_density_vector(sat1, "body")))
    assert np.all(np.isclose(B0, flux_density_vector(sat2, "body")))

    # The magnetic actor will oscillate slightly, following the Earth's magnetic field lines. (check for multiple steps)
    # The actor's magnetic field will not stay perfectly aligned with the Earth's field but needs to stay close.
    for i in range(20):
        sim.advance_time(200, 0)

        # Get the magnetic flux density vector:
        B = flux_density_vector(sat1)

        # B vector direction:
        B_direction = B / np.linalg.norm(B)

        # Angle between the B vector and the actor's magnetic dipole vector (which is in the pointing vector direction):
        angle = np.arccos(np.dot(B_direction, sat1.pointing_vector)) * 180 / np.pi

        # Check if the magnetic actor dipole moment vector does not deviate more than 1° from the  B vector.
        assert angle < 1

    # Check if the non-magnetic actor didn't rotate
    assert np.all(sat2.pointing_vector == initial_pointing_vector_eci)