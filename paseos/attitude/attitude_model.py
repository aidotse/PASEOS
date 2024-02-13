import numpy as np
import pykep as pk
from ..actors.spacecraft_actor import SpacecraftActor

from .disturbance_torques_utils import (
    compute_aerodynamic_torque,
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
    # Actor attitude in rad..
    _actor_attitude_in_rad = None
    # Actor angular velocity [rad/s].
    _actor_angular_velocity = None
    # Actor angular acceleation [rad/s^2].
    _actor_angular_acceleration = None
    # Actor pointing vector expressed in the body frame.
    _actor_pointing_vector_body = None
    # Actor pointing vector expressed in intertial frame.
    _actor_pointing_vector_eci = None
    # Attitude disturbances experienced by the actor.
    _disturbances = None

    def __init__(
        self,
        local_actor,
        # initial conditions:
        actor_initial_attitude_in_rad: list[float] = [0.0, 0.0, 0.0],
        actor_initial_angular_velocity: list[float] = [0.0, 0.0, 0.0],
        # pointing vector in body frame: (defaults to body z-axis)
        actor_pointing_vector_body: list[float] = [0.0, 0.0, 1.0],
        actor_residual_magnetic_field_body: list[float] = [0.0, 0.0, 0.0],
    ):
        """Creates an attitude model to model actor attitude based on
        initial conditions (initial attitude and angular velocity) and
        external disturbance torques.

        Args:
            actor (SpacecraftActor): Actor to model.
            actor_initial_attitude_in_rad (list of floats): Actor's initial attitude ([roll, pitch, yaw]) angles.
                Defaults to [0., 0., 0.].
            actor_initial_angular_velocity (list of floats): Actor's initial angular velocity vector.
                Defaults to [0., 0., 0.].
            actor_pointing_vector_body (list of floats): User defined vector in the Actor body. Defaults to [0., 0., 1]
            actor_residual_magnetic_field_body (list of floats): Actor's own magnetic field modeled as dipole moment vector.
                Defaults to [0., 0., 0.].
        """
        assert (isinstance(local_actor, SpacecraftActor)
            ), "local_actor must be a ""SpacecraftActor""."

        assert (
                np.asarray(actor_initial_attitude_in_rad).shape[0] == 3 and actor_initial_attitude_in_rad.ndim == 1
            ), "actor_initial_attitude_in_rad shall be [3] shaped."

        assert (
                np.asarray(actor_initial_angular_velocity).shape[0] == 3 and actor_initial_angular_velocity.ndim == 1
            ), "actor_initial_angular_velocity shall be [3] shaped."

        assert (
                np.asarray(actor_pointing_vector_body).shape[0] == 3 and actor_pointing_vector_body.ndim == 1
            ), "actor_pointing_vector_body shall be [3] shaped."

        assert (
                np.asarray(actor_residual_magnetic_field_body).shape[0] == 3 and actor_residual_magnetic_field_body.ndim == 1
            ), "actor_residual_magnetic_field_body shall be [3] shaped."

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

    def _nadir_vector(self):
        """Compute unit vector pointing towards earth, in the inertial frame.

        Returns:
            np array ([x, y, z]): unit nadir vector in ECIF (Earth-centered inertial frame)
        """
        u = np.array(self._actor.get_position(self._actor.local_time))
        return -u / np.linalg.norm(u)

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
            if self._actor.central_body != pk.earth:
                raise NotImplementedError("Models for torque disturbances are implemented only for Earth as a central body.")

            if TorqueDisturbanceModel.Aerodynamic in self._actor.attitude_disturbances:
                T += compute_aerodynamic_torque(
                    position,
                    velocity,
                    self._actor.geometric_model.mesh,
                    self.actor_attitude_in_rad,
                    current_temperature_K,
                )
            if TorqueDisturbanceModel.Gravitational in self._actor.attitude_disturbances:
                # Extract nadir vectors in different reference systems
                nadir_vector_in_rpy = eci_to_rpy(self._nadir_vector(), position, velocity)
                nadir_vector_in_body = rpy_to_body(nadir_vector_in_rpy, euler_angles)
                # Extract Earth rotation vector in different reference systems
                earth_rotation_vector_in_rpy = eci_to_rpy(np.array([0, 0, 1]), position, velocity)
                earth_rotation_vector_in_body = rpy_to_body(
                    earth_rotation_vector_in_rpy, euler_angles
                )
                # Accumulate torque due to gravity gradients
                T += compute_gravity_gradient_torque(
                    self._actor.central_body.planet,
                    nadir_vector_in_body,
                    earth_rotation_vector_in_body,
                    self._actor.body_moment_of_inertia_body,
                    np.linalg.norm(position),
                )
            if TorqueDisturbanceModel.Magnetic in self._actor.attitude_disturbances:
                time = self._actor.local_time
                T += compute_magnetic_torque(
                    m_earth=self._actor.central_body.magnetic_dipole_moment(time),
                    m_sat=self._actor_residual_magnetic_field_body,
                    position=self._actor.get_position(time),
                    velocity=self._actor.get_position_velocity(time)[1],
                    attitude=self._actor_attitude_in_rad,
                )
        return T

    def _calculate_angular_acceleration(self, current_temperature_K):
        """Calculate the spacecraft angular acceleration (external disturbance torques and gyroscopic accelerations).
        Args:
            current_temperature_K (float): current temperature in Kelvin.
        """

        # TODO in the future control torques could be added
        # Euler's equation for rigid body rotation: a = I^(-1) (T - w x (Iw))
        # with: a = angular acceleration, body_moment_of_inertia = inertia matrix, T = torque vector, w = angular velocity
        self._actor_angular_acceleration = np.linalg.inv(self._actor.body_moment_of_inertia_body) @ (
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

    @staticmethod
    def _frame_rotation(position, next_position, velocity):
        """Calculate the rotation vector of the RPY frame rotation within the inertial frame.
        This rotation component makes the actor body attitude stay constant w.r.t. inertial frame.

        Args:
            position (np.ndarray): actor position vector.
            next_position (np.ndarray): actor position vector in the next timestep.
            velocity (np.ndarray): actor velocity vector.

        Returns: rotation vector of RPY frame w.r.t. ECI frame expressed in the ECI frame.
        """
        # orbital plane normal unit vector: (p x v)/||p x v||
        orbital_plane_normal = np.cross(position, velocity) / np.linalg.norm(
            np.cross(position, velocity)
        )

        # rotation angle: arccos((p . p_previous) / (||p|| ||p_previous||))
        rpy_frame_rotation_angle_in_eci = np.arccos(
            np.linalg.multi_dot([position, next_position])
            / (np.linalg.norm(position) * np.linalg.norm(next_position))
        )

        # assign this scalar rotation angle to the vector perpendicular to rotation plane
        rpy_frame_rotation_vector_in_eci = orbital_plane_normal * rpy_frame_rotation_angle_in_eci

        # this rotation needs to be compensated in the rotation of the body frame, so its attitude stays fixed
        return -eci_to_rpy(rpy_frame_rotation_vector_in_eci, position, velocity)

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
        position, velocity = np.array(self._actor.get_position_velocity(self._actor.local_time)[1])

        # Initial body vectors expressed in rpy frame: (x, y, z, custom pointing vector)
        xb_rpy, yb_rpy, zb_rpy, pointing_vector_rpy = self._body_axes_in_rpy()

        # attitude change due to two rotations
        # rpy frame rotation, in inertial frame:
        theta_1 = self._frame_rotation(position, next_position, velocity)
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
