"""Tests to see whether the attitude and disturbance models work as intended"""

import numpy as np
import pykep as pk
import sys

sys.path.append("../..")
import paseos
from paseos import ActorBuilder, SpacecraftActor
from paseos.utils.reference_frame_transfer import eci_to_rpy, rpy_to_body


def attitude_model_test():
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


def magnetic_disturbance_test():
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
        m_earth = actor._attitude_model.earth_magnetic_dipole_moment()

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
            actor_attitude = np.array(actor.attitude_in_rad())
            return rpy_to_body(
                eci_to_rpy(B, actor_position, actor_velocity), actor_attitude
            )

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
    ActorBuilder.set_geometric_model(sat1, mass=100)
    ActorBuilder.set_geometric_model(sat2, mass=100)

    # Now, align the body magnetic dipole with the local Earth magnetic flux density vector
    # Earth magnetic flux density vector at start position is approximately:
    B0 = np.array([-3.18159529e-09, 1.02244882e-07, -3.72362170e-08])

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
        actor_residual_magnetic_field=actor_dipole,  # magnetic
    )

    ActorBuilder.set_attitude_model(
        sat2,
        actor_initial_angular_velocity=[0.0, 0.0, 0.0],
        actor_pointing_vector_body=initial_pointing_vector_body,
        actor_initial_attitude_in_rad=[0.0, 0.0, 0.0],
        actor_residual_magnetic_field=[0.0, 0.0, 0.0],  # non-magnetic
    )

    # Disturbances:
    ActorBuilder.set_disturbances(sat1, magnetic=True)
    ActorBuilder.set_disturbances(sat2, magnetic=True)

    # Initial pointing vector in Earth inertial frame
    initial_pointing_vector_eci = np.array(sat1.pointing_vector())
    # Check if pointing vectors in Earth inertial frame are equal
    assert np.all(sat1.pointing_vector() == sat2.pointing_vector())

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
        angle = np.arccos(np.dot(B_direction, sat1.pointing_vector())) * 180 / np.pi

        # Check if the magnetic actor dipole moment vector doesn't deviate more than 1° from the  B vector.
        assert angle < 1

    # Check if the non-magnetic actor didn't rotate
    assert np.all(sat2.pointing_vector() == initial_pointing_vector_eci)
