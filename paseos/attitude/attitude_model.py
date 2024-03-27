import numpy as np
import pykep as pk
from ..actors.spacecraft_actor import SpacecraftActor
from loguru import logger

from .disturbance_torques_utils import (
    compute_magnetic_torque,
    compute_gravity_gradient_torque,
)
from ..utils.reference_frame_transfer import (
    eci_to_rpy,
    rpy_to_eci,
    body_to_rpy,
    rodrigues_rotation,
    get_rpy_angles,
    rotate_body_vectors,
    rpy_to_body,
    frame_rotation,
)

from enum import Enum


class TorqueDisturbanceModel(Enum):
    """Describes the different torque disturbance models supported.
    1 - SpacePlot
    """

    Aerodynamic = 1
    Gravitational = 2
    Magnetic = 3


class AttitudeModel:
    """This model describes the attitude (Roll, Pitch and Yaw) evolution of a spacecraft actor.
    Starting from an initial attitude and angular velocity, the spacecraft response to disturbance torques is simulated.

    The model allows for one pointing vector to be defined in the actor body frame for visualization and possibly
    could be used for future antenna pointing applications. Its position in time within the Earth-centered inertial
    frame is also calculated alongside the general body attitude.

    The attitude calculations are based in three reference frames, refer to reference_frame_transfer.py in utils folder.
    """

    # Spacecraft actor.
    _actor = None
    # Actor attitude in rad.
    _actor_attitude_in_rad = None
    # Actor angular velocity expressed in body frame [rad/s].
    _actor_angular_velocity = None
    # Actor angular acceleation expressed in body frame [rad/s^2].
    _actor_angular_acceleration = None
    # Actor pointing vector expressed in the body frame.
    _actor_pointing_vector_body = None
    # Actor pointing vector expressed in intertial frame.
    _actor_pointing_vector_eci = None
    # Attitude disturbances experienced by the actor.
    _disturbances = None
    # Accommodation parameter for Aerodynamic torque disturbance calculations.
    # Please refer to: "Roto-Translational Spacecraft Formation Control Using Aerodynamic Forces";
    # Ran. S, Jihe W., et al.; 2017.
    _accommodation_coefficient = None
    # Earth J2 coefficient.
    _J2_coefficient = 1.0826267e-3  # Dimensionless constant.
    # Universal gas constant
    _R_gas = 8.314462  # [J/(K mol)]

    def __init__(
        self,
        local_actor,
        # initial conditions:
        actor_initial_attitude_in_rad: list[float] = [0.0, 0.0, 0.0],
        actor_initial_angular_velocity: list[float] = [0.0, 0.0, 0.0],
        # pointing vector in body frame: (defaults to body z-axis)
        actor_pointing_vector_body: list[float] = [0.0, 0.0, 1.0],
        actor_residual_magnetic_field_body: list[float] = [0.0, 0.0, 0.0],
        accommodation_coefficient: float = 0.85,
    ):
        """Creates an attitude model to model actor attitude based on
        initial conditions (initial attitude and angular velocity) and
        external disturbance torques.

        Args:
            actor (SpacecraftActor): Actor to model.
            actor_initial_attitude_in_rad (list of floats, optional): Actor's initial attitude ([roll, pitch, yaw]) angles.
                Defaults to [0., 0., 0.].
            actor_initial_angular_velocity (list of floats, optional) in the body frame: Actor's initial angular velocity
                vector. Defaults to [0., 0., 0.].
            actor_pointing_vector_body (list of floats, optional): User defined vector in the Actor body.
                Defaults to [0., 0., 1].
            actor_residual_magnetic_field_body (list of floats, optional): Actor's own magnetic field modeled
                as dipole moment vector. Defaults to [0., 0., 0.].
            accommodation_coefficient (float): Accommodation coefficient used for Aerodynamic torque disturbance calculation.
                Defaults to 0.85.
        """
        assert isinstance(local_actor, SpacecraftActor), (
            "local_actor must be a " "SpacecraftActor" "."
        )

        logger.trace("Initializing thermal model.")
        self._actor = local_actor
        # convert to np.ndarray
        self._actor_attitude_in_rad = np.array(actor_initial_attitude_in_rad)
        self._actor_angular_velocity = np.array(actor_initial_angular_velocity)

        # normalize inputted pointing vector & convert to np.ndarray
        self._actor_pointing_vector_body = np.array(actor_pointing_vector_body) / np.linalg.norm(
            np.array(actor_pointing_vector_body)
        )

        # pointing vector expressed in Earth-centered inertial frame
        self._actor_pointing_vector_eci = rpy_to_eci(
            body_to_rpy(self._actor_pointing_vector_body, self._actor_attitude_in_rad),
            np.array(self._actor.get_position(self._actor.local_time)),
            np.array(self._actor.get_position_velocity(self._actor.local_time)[1]),
        )

        # angular velocity vector expressed in Earth-centered inertial frame
        self._actor_angular_velocity_eci = rpy_to_eci(
            body_to_rpy(self._actor_angular_velocity, self._actor_attitude_in_rad),
            np.array(self._actor.get_position(self._actor.local_time)),
            np.array(self._actor.get_position_velocity(self._actor.local_time)[1]),
        )

        # actor residual magnetic field (modeled as dipole)
        self._actor_residual_magnetic_field_body = np.array(actor_residual_magnetic_field_body)

        # Accommodation coefficient
        self._accommodation_coefficient = accommodation_coefficient

    def _nadir_vector(self):
        """Compute unit vector pointing towards earth, in the inertial frame.

        Returns:
            np array ([x, y, z]): unit nadir vector in ECIF (Earth-centered inertial frame)
        """
        u = np.array(self._actor.get_position(self._actor.local_time))
        nadir_vector = -u / np.linalg.norm(u)
        logger.trace(f"Nadir vector: {nadir_vector}")
        return nadir_vector

    def compute_disturbance_torque(self, position, velocity, euler_angles, current_temperature_K):
        """Compute total torque due to user-specified disturbances.

        Args:
            position (np.ndarray): position vector of RPY reference frame wrt ECI frame.
            velocity (np.ndarray): velocity of the spacecraft in earth reference frame, centered on spacecraft.
            euler_angles (np.ndarray): [roll, pitch, yaw] in radians.
            current_temperature_K (float): current temperature in Kelvin.
        Returns:
            np.array([Tx, Ty, Tz]): total combined torques in Nm expressed in the spacecraft body frame.
        """
        # Transform the earth rotation vector to the body reference frame, assuming the rotation vector is the z-axis
        # of the earth-centered-inertial (eci) frame.
        T = np.array([0.0, 0.0, 0.0])

        if self._disturbances is not None:
            if self._actor.central_body.planet.name != "earth":
                raise NotImplementedError(
                    "Models for torque disturbances are implemented only for Earth as a central body."
                )

            # TODO Add solar disturbances. Refer to issue: https://github.com/aidotse/PASEOS/issues/206

            if TorqueDisturbanceModel.Aerodynamic in self._actor.attitude_disturbances:
                # TODO improve integration and testing of aerodynamic model.
                # Refer to issue: https://github.com/aidotse/PASEOS/issues/207
                raise ValueError("Aerodynamic torque disturbance model is not implemented.")

            if TorqueDisturbanceModel.Gravitational in self._actor.attitude_disturbances:
                # Extract nadir vectors in different reference systems
                nadir_vector_in_rpy = eci_to_rpy(self._nadir_vector(), position, velocity)
                nadir_vector_in_body = rpy_to_body(nadir_vector_in_rpy, euler_angles)
                # Extract Earth rotation vector in different reference systems
                earth_rotation_vector_in_rpy = eci_to_rpy(np.array([0, 0, 1]), position, velocity)
                earth_rotation_vector_in_body = rpy_to_body(
                    earth_rotation_vector_in_rpy, euler_angles
                )
                # Computing gravitational torque
                gravitational_torque = compute_gravity_gradient_torque(
                    self._actor.central_body.planet,
                    nadir_vector_in_body,
                    earth_rotation_vector_in_body,
                    self._actor.body_moment_of_inertia_body,
                    np.linalg.norm(position),
                    self._J2_coefficient,
                )
                logger.debug(f"Gravitational torque: f{gravitational_torque}")
                # Accumulate torque due to gravity gradients
                T += gravitational_torque

            if TorqueDisturbanceModel.Magnetic in self._actor.attitude_disturbances:
                time = self._actor.local_time
                # Computing magnetic torque
                magnetic_torque = compute_magnetic_torque(
                    m_earth=self._actor.central_body.magnetic_dipole_moment(time),
                    m_sat=self._actor_residual_magnetic_field_body,
                    position=self._actor.get_position(time),
                    velocity=self._actor.get_position_velocity(time)[1],
                    attitude=self._actor_attitude_in_rad,
                )
                logger.debug(f"Magnetic torque: f{magnetic_torque}")
                # Accumulating magnetic torque
                T += magnetic_torque

            logger.trace(f"Disturbance torque: f{T}")
        return T

    def _calculate_angular_acceleration(self, current_temperature_K):
        """Calculate the spacecraft angular acceleration (external disturbance torques and gyroscopic accelerations).
        Args:
            current_temperature_K (float): current temperature in Kelvin.
        """

        # TODO in the future control torques could be added
        # Euler's equation for rigid body rotation: a = I^(-1) (T - w x (Iw))
        # with: a = angular acceleration, body_moment_of_inertia = inertia matrix, T = torque vector, w = angular velocity
        self._actor_angular_acceleration = np.linalg.inv(
            self._actor.body_moment_of_inertia_body
        ) @ (
            self.compute_disturbance_torque(
                position=np.array(self._actor.get_position(self._actor.local_time)),
                velocity=np.array(self._actor.get_position_velocity(self._actor.local_time)[1]),
                euler_angles=self._actor_attitude_in_rad,
                current_temperature_K=current_temperature_K,
            )
            - np.cross(
                self._actor_angular_velocity,
                self._actor.body_moment_of_inertia_body @ self._actor_angular_velocity,
            )
        )

    def _body_rotation(self, dt, current_temperature_K):
        """Calculates the rotation vector around which the spacecraft body rotates
        based on angular acceleration, velocity, and current temperature.

        Args:
            dt (float): time to advance.
            current_temperature_K (float): current temperature in Kelvin.

        Returns: rotation vector of spacecraft body expressed in the RPY frame.
        """
        # Calculate angular acceleration
        self._calculate_angular_acceleration(current_temperature_K)

        # Add angular velocity
        self._actor_angular_velocity += self._actor_angular_acceleration * dt

        # Body rotation vector:
        body_rotation = self._actor_angular_velocity * dt

        # Return rotation vector in RPY frame
        return body_to_rpy(body_rotation, self._actor_attitude_in_rad)

    def _body_axes_in_rpy(self):
        """Transforms vectors expressed in the spacecraft body frame to the roll pitch yaw frame.
        Vectors: - x, y, z axes
                 - user specified pointing vector

        Returns: transformed vectors.
        """
        # principal axes:
        x = body_to_rpy(np.array([1, 0, 0]), self._actor_attitude_in_rad)
        y = body_to_rpy(np.array([0, 1, 0]), self._actor_attitude_in_rad)
        z = body_to_rpy(np.array([0, 0, 1]), self._actor_attitude_in_rad)

        # pointing vector:
        p = body_to_rpy(self._actor_pointing_vector_body, self._actor_attitude_in_rad)
        return x, y, z, p

    def update_attitude(self, dt, current_temperature_K):
        """Updates the actor attitude based on initial conditions and disturbance torques over time.

        Args:
            dt (float): how far to advance the attitude computation.
            current_temperature_K (float): current actor temperature in Kelvin.
        """
        # time
        t = self._actor.local_time

        # next position
        next_position = np.array(
            self._actor.get_position(pk.epoch(t.mjd2000 + dt * pk.SEC2DAY, "mjd2000"))
        )

        # position, velocity
        position, velocity = np.array(self._actor.get_position_velocity(self._actor.local_time))

        # Initial body vectors expressed in rpy frame: (x, y, z, custom pointing vector)
        xb_rpy, yb_rpy, zb_rpy, pointing_vector_rpy = self._body_axes_in_rpy()

        # attitude change due to two rotations
        # rpy frame rotation, in inertial frame:
        theta_1 = frame_rotation(position, next_position, velocity)
        # body rotation due to its physical rotation
        theta_2 = self._body_rotation(dt, current_temperature_K)

        # rotate the body vectors in rpy frame with frame rotation
        xb_rpy, yb_rpy, zb_rpy, pointing_vector_rpy = rotate_body_vectors(
            xb_rpy, yb_rpy, zb_rpy, pointing_vector_rpy, theta_1
        )

        # rotate the body rotation vector as well
        theta_2 = rodrigues_rotation(theta_2, theta_1)
        # rotate the body vectors in rpy frame with body rotation
        xb_rpy, yb_rpy, zb_rpy, pointing_vector_rpy = rotate_body_vectors(
            xb_rpy, yb_rpy, zb_rpy, pointing_vector_rpy, theta_2
        )

        # update new attitude in ECI:
        self._actor_attitude_in_rad = get_rpy_angles(xb_rpy, yb_rpy, zb_rpy)

        # update new angular velocity vector in ECI:
        self._actor_angular_velocity_eci = rpy_to_eci(
            body_to_rpy(self._actor_angular_velocity, self._actor_attitude_in_rad),
            next_position,
            velocity,
        )
        # update pointing vector
        self._actor_pointing_vector_eci = rpy_to_eci(pointing_vector_rpy, next_position, velocity)

        logger.trace(f"Actor's new attitude (Yaw, Pitch, Roll) is f{self._actor_attitude_in_rad}")
        logger.trace(
            f"Actor's new angular velocity (ECI) vector is f{self._actor_angular_velocity_eci}"
        )
        logger.trace(f"Actor's new pointing vector (ECI) is f{self._actor_pointing_vector_eci}")
