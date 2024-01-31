import numpy as np
import pykep as pk

from paseos.attitude.disturbance_calculations import (
    calculate_aero_torque,
    calculate_magnetic_torque,
    calculate_grav_torque,
)
from paseos.utils.reference_frame_transfer import (
    eci_to_rpy,
    rpy_to_eci,
    body_to_rpy,
    rodrigues_rotation,
    get_rpy_angles,
    rotate_body_vectors,
    rpy_to_body,
)


class AttitudeModel:
    """This model describes the attitude (Roll, Pitch and Yaw) evolution of a spacecraft actor.
    Starting from an initial attitude and angular velocity, the spacecraft response to disturbance torques is simulated.

    The model allows for one pointing vector to be defined in the actor body frame for visualization and possibly
    could be used for future antenna pointing applications. Its position in time within the Earth-centered inertial
    frame is also calculated alongside the general body attitude.

    The attitude calculations are based in three reference frames, refer to reference_frame_transfer.py in utils folder.
    """

    _actor = None

    _actor_attitude_in_rad = None
    _actor_angular_velocity = None
    _actor_angular_acceleration = None

    _actor_pointing_vector_body = None
    _actor_pointing_vector_eci = None

    def __init__(
        self,
        local_actor,
        # initial conditions:
        actor_initial_attitude_in_rad: list[float] = [0., 0., 0.],
        actor_initial_angular_velocity: list[float] = [0., 0., 0.],
        # pointing vector in body frame: (defaults to body z-axis)
        actor_pointing_vector_body: list[float] = [0., 0., 1.]
    ):
        """ Creates an attitude model to model actor attitude based on
        initial conditions (initial attitude and angular velocity) and
        external disturbance torques.

        Args:
            actor (SpacecraftActor): Actor to model.
            actor_initial_attitude_in_rad (list of floats): Actor's initial attitude ([roll, pitch, yaw]) angles.
                Defaults to [0., 0., 0.].
            actor_initial_angular_velocity (list of floats): Actor's initial angular velocity vector.
                Defaults to [0., 0., 0.].
            actor_pointing_vector_body (list of floats): User defined vector in the Actor body. Defaults to [0., 0., 1]
        """
        self._actor = local_actor
        # convert to np.ndarray
        self._actor_attitude_in_rad = np.array(actor_initial_attitude_in_rad)
        self._actor_angular_velocity = np.array(actor_initial_angular_velocity)

        # normalize inputted pointing vector & convert to np.ndarray
        self._actor_pointing_vector_body = np.array(
            actor_pointing_vector_body
        ) / np.linalg.norm(np.array(actor_pointing_vector_body))

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

    def _nadir_vector(self):
        """Compute unit vector pointing towards earth, in the inertial frame.

        Returns:
            np array ([x, y, z]): unit nadir vector in ECIF (Earth-centered inertial frame)
        """
        u = np.array(self._actor.get_position(self._actor.local_time))
        return -u / np.linalg.norm(u)


    def calculate_disturbance_torque(self, position, velocity, euler_angles):
        """Compute total torque due to user-specified disturbances.

        Args:
            position (np.ndarray): position vector of RPY reference frame wrt ECI frame
            velocity (np.ndarray): velocity of the spacecraft in earth reference frame, centered on spacecraft
            euler_angles (np.ndarray): [roll, pitch, yaw] in radians

        Returns:
            np.array([Tx, Ty, Tz]): total combined torques in Nm expressed in the spacecraft body frame.
        """

        # Transform the earth rotation vector to the body reference frame, assuming the rotation vector is the z-axis
        # of the earth-centered-inertial (eci) frame


        T = np.array([0.0, 0.0, 0.0])

        if self._actor.has_attitude_disturbances:
            if "aerodynamic" in self._actor.get_disturbances():
                T += calculate_aero_torque()
            if "gravitational" in self._actor.get_disturbances():
                nadir_vector_in_rpy = eci_to_rpy(self.nadir_vector(), position, velocity)
                nadir_vector_in_body = rpy_to_body(nadir_vector_in_rpy, euler_angles)
                earth_rotation_vector_in_rpy = eci_to_rpy(np.array([0, 0, 1]), position, velocity)
                earth_rotation_vector_in_body = rpy_to_body(earth_rotation_vector_in_rpy, euler_angles)
                T += calculate_grav_torque(nadir_vector_in_body,earth_rotation_vector_in_body,
                                           self._actor._moment_of_inertia(), np.linalg.norm(position))
            if "magnetic" in self._actor.get_disturbances():
                T += calculate_magnetic_torque()
        return T

    def _calculate_angular_acceleration(self):
        """Calculate the spacecraft angular acceleration (external disturbance torques and gyroscopic accelerations)."""
        # TODO in the future control torques could be added

        # moment of Inertia matrix:
        I = self._actor._moment_of_inertia()

        # Euler's equation for rigid body rotation: a = I^(-1) (T - w x (Iw))
        # with: a = angular acceleration, I = inertia matrix, T = torque vector, w = angular velocity
        self._actor_angular_acceleration = np.linalg.inv(I) @ (

            self.calculate_disturbance_torque(position=np.array(self._actor.get_position(self._actor.local_time)),
                                              velocity=np.array(self._actor.get_position_velocity(self._actor.local_time)[1]),
                                              euler_angles=self._actor_attitude_in_rad)
            - np.cross(self._actor_angular_velocity, I @ self._actor_angular_velocity)
        )

    def _body_rotation(self, dt):
        """Calculates the rotation vector around which the spacecraft body rotates
        based on angular acceleration and velocity.

        Args:
            dt (float): time to advance.

        Returns: rotation vector of spacecraft body expressed in the RPY frame.
        """
        # Calculate angular acceleration
        self._calculate_angular_acceleration()

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
        rpy_frame_rotation_vector_in_eci = (
            orbital_plane_normal * rpy_frame_rotation_angle_in_eci
        )

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

    def update_attitude(self, dt):
        """Updates the actor attitude based on initial conditions and disturbance torques over time.

        Args:
            dt (float): How far to advance the attitude computation.
        """
        # time
        t = self._actor.local_time

        # position
        position = np.array(self._actor.get_position(t))

        # next position
        next_position = np.array(
            self._actor.get_position(pk.epoch(t.mjd2000 + dt * pk.SEC2DAY, "mjd2000"))
        )

        # velocity
        velocity = np.array(
            self._actor.get_position_velocity(self._actor.local_time)[1]
        )

        # Initial body vectors expressed in rpy frame: (x, y, z, custom pointing vector)
        xb_rpy, yb_rpy, zb_rpy, pointing_vector_rpy = self._body_axes_in_rpy()

        # attitude change due to two rotations
        # rpy frame rotation, in inertial frame:
        theta_1 = self._frame_rotation(position, next_position, velocity)
        # body rotation due to its physical rotation
        theta_2 = self._body_rotation(dt)

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
        self._actor_pointing_vector_eci = rpy_to_eci(
            pointing_vector_rpy, next_position, velocity
        )
