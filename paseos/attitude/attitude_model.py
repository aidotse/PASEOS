from loguru import logger
import pykep as pk
import numpy as np

from paseos.attitude.disturbance_calculations import (calculate_aero_torque,
                                                      calculate_magnetic_torque,
                                                      calculate_grav_torque)
from paseos.attitude.reference_frame_transfer import (eci_to_rpy,
                                                      rpy_to_eci,
                                                      rpy_to_body,
                                                      body_to_rpy,
                                                      get_euler)

class AttitudeModel:


    _actor = None
    _actor_attitude_in_rad = None
    _actor_angular_velocity = None
    _actor_angular_acceleration = None
    _actor_pointing_vector_rpy = None
    _actor_pointing_vector_eci = None

    _actor_prev_pos = None
    def __init__(
            self,
            local_actor,
            # initial angular conditions: (defaults to 0)
            actor_initial_attitude_in_rad: list[float] = [0, 0, 0],
            actor_initial_angular_velocity: list[float] = [0, 0, 0],
            actor_initial_angular_acceleration: list[float] = [0, 0, 0],
            # trial:
            actor_initial_pointing_vector_rpy: list[float] = [0,0,1],            # make this better
            actor_initial_pointing_vector_eci: list[float] = None,

            actor_initial_previous_position = [1.e+07, 1.e-03, 1.e-03]
            ## add args with default value = None, if
            # actor_dipole
            # actor_drag_coefficient
            # body_J2
            #
    ):
        self._actor = local_actor
        self._actor_attitude_in_rad = actor_initial_attitude_in_rad
        self._actor_angular_velocity = actor_initial_angular_velocity
        self._actor_angular_acceleration = actor_initial_angular_acceleration

        self._actor_pointing_vector_rpy = actor_initial_pointing_vector_rpy
        self._actor_pointing_vector_eci = actor_initial_pointing_vector_eci

        self._actor_prev_pos = actor_initial_previous_position


    def nadir_vector(self):
        """computes unit vector pointing towards earth, inertial body frame

        Returns:
            np array ([x, y, z]): unit nadir vector in ECIF (Earth-centered inertial frame)
        """
        u = np.array(self._actor.get_position(self._actor.local_time))
        return -u/np.linalg.norm(u)

    def calculate_disturbance_torque(self):
        """Computes total torque due to user specified disturbances

        Returns:
            list [Tx, Ty, Tz]: total combined torques in Nm
        """

        T = np.array([0,0,0])
        if "aerodynamic" in self._actor.get_disturbances():
            T += calculate_aero_torque()
        if "gravitational" in self._actor.get_disturbances():
            T += calculate_grav_torque()
        if "magnetic" in self._actor.get_disturbances():
            T += calculate_magnetic_torque()
        return T

    def move_pointing_vector(self, pos, vel):
        self._actor_pointing_vector_eci = rpy_to_eci(self._actor_pointing_vector_rpy,
                                                     pos,
                                                     vel)
        self._actor_pointing_vector_eci = (self._actor_pointing_vector_eci +
                                           np.array(self._actor_prev_pos) -
                                           pos)

        #print(np.array(pos) - np.array(self._actor_prev_pos))
    def update_attitude(self, dt):
        """

        Args:
            dt (float): How far to advance the attitude computation.

        Returns:
            np array
        """
        position = self._actor.get_position(self._actor.local_time)
        velocity = self._actor.get_position_velocity(self._actor.local_time)[1]

        self.move_pointing_vector(position, velocity)
        self._actor_pointing_vector_rpy = eci_to_rpy(self._actor_pointing_vector_eci,
                                                     position,
                                                     velocity)
        # calculate euler angles between nadir and new pointing vector.

        # constants:
        # self._actor_I =
        # self._actor_mass = 50

        I = np.array([[50,0,0], [0,50,0], [0,0,50]])

        # disturbance torque vector
        disturbance_torque = self.calculate_disturbance_torque()
        disturbance_torque = np.array([0,0,0])  # placeholder

        # dynamics:
        # acceleration
        """
        self._actor_angular_acceleration = (
                np.linalg.inv(I) @ (disturbance_torque -
                                    np.cross(np.array(self._actor_angular_velocity),
                                             I @ np.array(self._actor_angular_velocity))))

        """
        self._actor_angular_acceleration = np.linalg.inv(I) @ disturbance_torque
        # velocity
        self._actor_angular_velocity += self._actor_angular_acceleration * dt
        # update attitude
        self._actor_attitude_in_rad += self._actor_angular_velocity * dt + get_euler(self._actor_pointing_vector_rpy,
                                                                                     self.nadir_vector())
        #print(get_euler(self._actor_pointing_vector_rpy, self.nadir_vector()))
        self._actor_attitude_in_rad = np.arctan2(
            np.sin(self._actor_attitude_in_rad), np.cos(self._actor_attitude_in_rad))
        # previous position (to be used in next computation)
        self._actor_prev_pos = position