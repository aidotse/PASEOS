import numpy
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
    _actor_pointing_vector_eci = None

    #_actor_prev_pos = None
    def __init__(
            self,
            local_actor,
            # initial angular conditions: (defaults to 0)
            actor_initial_attitude_in_rad: list[float] = [0, 0, 0],
            actor_initial_angular_velocity: list[float] = [0, 0, 0],
            actor_initial_angular_acceleration: list[float] = [0, 0, 0],
            # trial:
            # actor_initial_pointing_vector_rpy: list[float] = [0,0,1],            # make this better
            # actor_initial_pointing_vector_eci: list[float] = None,

            #actor_initial_previous_position = [1.e+07, 1.e-03, 1.e-03]
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

        #self._actor_pointing_vector_rpy = actor_initial_pointing_vector_rpy
        #self._actor_pointing_vector_eci = actor_initial_pointing_vector_eci
        if actor_initial_attitude_in_rad == [0, 0, 0]:
            self._actor_pointing_vector_eci = self.nadir_vector()
        else:
            self._actor_pointing_vector_eci = rpy_to_eci(np.ndarray.tolist(      # todo: consistency in ndarray or lists
                body_to_rpy([0,0,1], actor_initial_attitude_in_rad)),
                self._actor.get_position(self._actor.local_time),
                self._actor.get_position_velocity(self._actor.local_time)[1])

        #self._actor_prev_pos = actor_initial_previous_position


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

    def update_attitude(self, dt):
        """

        Args:
            dt (float): How far to advance the attitude computation.

        Returns:
            np array
        """

        # define position, previous position, velocity vectors
        # and euler angles (between the pointing vector in SBF and (0, 0, 1) z vector in RPY)

        #################################### STARTING CONDITIONS OF UPDATE ATTITUDE ####################################
        # position
        position = self._actor.get_position(self._actor.local_time)
        # previous position (will be None at first timestep)
        if not self._actor._previous_position:
            previous_position = position
        else:
            previous_position = self._actor._previous_position
        # velocity
        velocity = self._actor.get_position_velocity(self._actor.local_time)[1]

        # nadir pointing vector in ECI
        nadir_eci = self.nadir_vector()

        # update the euler angles (attitude) of the spacecraft body wrt rpy frame
        attitude_eci = get_euler(nadir_eci, self._actor_pointing_vector_eci)                           # rotation in ECI
        self._actor_attitude_in_rad = eci_to_rpy(attitude_eci, position, velocity, translation=False)  # rotation in RPY
        euler = self._actor_attitude_in_rad

        # body angular velocity wrt RPY frame after timestep dt
        angular_velocity_body_wrt_rpy = np.array(self._actor_attitude_in_rad) / dt
        self._actor_angular_velocity = rpy_to_body(np.ndarray.tolist(angular_velocity_body_wrt_rpy), euler)

        # constants:
        # self._actor_I = (to do: from geometric model)
        # self._actor_mass = 50

        I = np.array([[50, 0, 0],
                      [0, 50, 0],
                      [0, 0, 50]])

        # disturbance torque vector
        # disturbance_torque = self.calculate_disturbance_torque()
        disturbance_torque = np.array([0,0,0])  # placeholder. IN SBF


        # dynamics:
        ####################################### ADD DISTURBANCE, UPDATE ATTITUDE #######################################

        # angular_velocity_sbf_wrt_rpy = self._actor_angular_velocity
        # acceleration euler equation for rigid body rotation (apply disturbance torques)

        self._actor_angular_acceleration = (
                np.linalg.inv(I) @ (disturbance_torque -
                                    np.cross(np.array(angular_velocity_body_wrt_rpy),
                                             I @ np.array(angular_velocity_body_wrt_rpy))))
        # new angular velocity of body frame wrt RPY
        # todo: check time when angular velocity of body wrt rpy is calculated
        angular_velocity_body_wrt_rpy = (angular_velocity_body_wrt_rpy +
                                body_to_rpy(self._actor_angular_acceleration, euler) * dt)

        self._actor_angular_velocity = rpy_to_body(angular_velocity_body_wrt_rpy, euler)
        # angular velocity of the RPY frame wrt ECI
        etha = -(np.arccos(np.linalg.multi_dot([position, previous_position]) /
                         (np.linalg.norm(position)*np.linalg.norm(previous_position)))) / dt * 0
            #  ^ minus because rotation of the spacecraft cg is in negative y direction in RPY

        angular_velocity_of_rpy_wrt_eci = rpy_to_eci([0, etha, 0], position, velocity, translation=False)

        # angular velocity of the spacecraft body wrt inertial frame
        angular_velocity_body_wrt_eci = (rpy_to_eci(angular_velocity_body_wrt_rpy, position, velocity, translation=False) +
                                       angular_velocity_of_rpy_wrt_eci)

        # update attitude
        if all(np.isclose(angular_velocity_of_rpy_wrt_eci, numpy.zeros(3))):
            k = np.zeros(3)
        else:
            k = angular_velocity_body_wrt_eci / np.linalg.norm(angular_velocity_body_wrt_eci)
        theta = np.linalg.norm(angular_velocity_body_wrt_eci) * dt
        P = self._actor_pointing_vector_eci
        P = (P * np.cos(theta) +
                                           (np.cross(k, P) * np.sin(theta)) +
                                           k * (np.linalg.multi_dot([k, P])) * (1 - np.cos(theta)))
        # normalize pointing vector
        self._actor_pointing_vector_eci = P / np.linalg.norm(P)
        #self._actor_attitude_in_rad += self._actor_angular_velocity * dt + get_euler(self._actor_pointing_vector_rpy,
        #                                                                             self.nadir_vector())
        self._actor_attitude_in_rad = get_euler(
            eci_to_rpy(self._actor_pointing_vector_eci, position, velocity, translation=False), [0,0,1])

        self._actor_attitude_in_rad = np.arctan2(
            np.sin(self._actor_attitude_in_rad), np.cos(self._actor_attitude_in_rad))
