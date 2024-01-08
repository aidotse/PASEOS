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
                                                      rodriguez_rotation,
                                                      get_rpy_angles,
                                                      rotate_body_vectors)

class AttitudeModel:


    _actor = None
    _actor_attitude_in_rad = None
    _actor_angular_velocity = None
    _actor_angular_acceleration = None

    _actor_pointing_vector_body = None
    _actor_pointing_vector_eci = None

    #_actor_prev_pos = None
    def __init__(
            self,
            local_actor,
            # initial angular conditions: (defaults to 0)
            actor_initial_attitude_in_rad: list[float] = [0, 0, 0],
            actor_initial_angular_velocity: list[float] = [0, 0, 0],
            actor_initial_angular_acceleration: list[float] = [0, 0, 0],
            actor_pointing_vector_body: list[float] = [0,0,1] # todo: letting user specify attitude and pointing vector doesn't make sense
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
        # pointing vectors: default body: z-axis, eci: initial nadir pointing
        # normalize inputted pointing vector
        self._actor_pointing_vector_body = (np.array(actor_pointing_vector_body) /
                                            np.linalg.norm(np.array(actor_pointing_vector_body)))
        """
        if actor_initial_attitude_in_rad == [0, 0, 0]:
            self._actor_pointing_vector_eci = self.nadir_vector()
        else:
            self._actor_pointing_vector_eci = rpy_to_eci(np.ndarray.tolist(      # todo: consistency in ndarray or lists
                body_to_rpy(actor_pointing_vector_body, actor_initial_attitude_in_rad)),
                self._actor.get_position(self._actor.local_time),
                self._actor.get_position_velocity(self._actor.local_time)[1])
        """
        # todo: make function transforming a vector from body to eci
        # todo: consistency in ndarray or lists
        # todo: allow for initial attitude
        # todo: positive roll seems to result in negative rotations
        self._actor_pointing_vector_eci = rpy_to_eci(
            body_to_rpy(self._actor_pointing_vector_body, actor_initial_attitude_in_rad),
            self._actor.get_position(self._actor.local_time),
            self._actor.get_position_velocity(self._actor.local_time)[1])
        self._actor_t = 0
        self._actor_starting_position = self._actor.get_position(self._actor.local_time)
        # can't do this, it messes up "previous position"
        #self._actor_starting_velocity = self._actor.get_position_velocity(self._actor.local_time)[1]
        #self._actor_orbital_plane_normal = (np.cross(self._actor_starting_position,
        #                                             self._actor_starting_velocity) /
        #                                    np.linalg.norm(np.cross(self._actor_starting_position,
        #                                                            self._actor_starting_velocity)))
        self._actor_orbital_plane_normal = None
        self._actor_body_rotation = np.array([0.0,0.0,0.0])

        self._actor_theta_1 = np.array([0.0,0.0,0.0])
        #self._actor_theta_2 = np.array([0.0,0.0,0.0])
        self._actor_theta_2 = np.array([0.0,0.0,0.0])

        #self._actor_xb_rpy = np.array([])
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
        self._actor_attitude_in_rad = eci_to_rpy(attitude_eci, position, velocity, translation=False) # rotation in RPY
        euler = self._actor_attitude_in_rad

        # body angular velocity wrt RPY frame after timestep dt
        angular_velocity_body_wrt_rpy = np.array(self._actor_attitude_in_rad) / dt
        self._actor_angular_velocity += rpy_to_body(np.ndarray.tolist(angular_velocity_body_wrt_rpy), euler)

        # constants:
        # self._actor_I = (to do: from geometric model)
        # self._actor_mass = 50

        I = np.array([[50, 0, 0],
                      [0, 50, 0],
                      [0, 0, 50]])

        # disturbance torque vector
        # disturbance_torque = self.calculate_disturbance_torque()
        disturbance_torque = np.array([0,100,0])  # placeholder. IN SBF


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
                         (np.linalg.norm(position)*np.linalg.norm(previous_position)))) / dt
            #  ^ minus because rotation of the spacecraft cg is in negative y direction in RPY

        angular_velocity_of_rpy_wrt_eci = rpy_to_eci([0, etha, 0], position, velocity, translation=False)

        # angular velocity of the spacecraft body wrt inertial frame
        angular_velocity_body_wrt_eci = (rpy_to_eci(angular_velocity_body_wrt_rpy, position, velocity, translation=False) +
                                       angular_velocity_of_rpy_wrt_eci)

        # update attitude

        self._actor_pointing_vector_eci = rpy_to_eci(body_to_rpy([0,0,1], self._actor_attitude_in_rad), position,
                                                     velocity, translation=False)
        self._actor_pointing_vector_eci[np.isclose(self._actor_pointing_vector_eci, np.zeros(3))] = 0

        self._actor_attitude_in_rad = np.arctan2(
            np.sin(self._actor_attitude_in_rad), np.cos(self._actor_attitude_in_rad))
        """
        """
        # this code works, but not for an initial attitude (wrong maths), commented out to implement that
        #################################### STARTING CONDITIONS OF UPDATE ATTITUDE ####################################
        # position
        position = self._actor.get_position(self._actor.local_time)

        # previous position (will be None at first timestep)
        previous_position = self._actor._previous_position
        # call previous position before velocity, as "get_position_velocity" sets previous position to current one
        # todo: velocity function starts previous position... when initializing pointing vector,
        #       looks like this means next line is not needed:
        # todo: find correct way of relating roll, pitch, yaw angles to a vector (to have initial attitude)
        if not previous_position:  # first timestep

            # velocity, called only to update previous position.
            velocity = self._actor.get_position_velocity(self._actor.local_time)[1]
            starting_position = position

        else:
            # step:
            step = self._actor_t

            # velocity
            velocity = self._actor.get_position_velocity(self._actor.local_time)[1]

            # orbital plane normal unit vector
            self._actor_orbital_plane_normal = (np.cross(position, velocity) /
                                                 np.linalg.norm(np.cross(position, velocity)))

            # attitude change due to two rotations:
            #   theta_1: rotation of the body frame wrt RPY, because of its fixed attitude in the inertial frame.
            #   theta_2: rotation of the body frame wrt RPY due to the body angular velocity * dt
            # todo: both thetas are negative. change?
            # theta_1:
            # rotation angle: arccos( (p . p_previous) / (||p|| ||p_previous||) )
            rpy_inertial_rotation_angle = np.arccos(np.linalg.multi_dot([position, previous_position]) /
                                                    (np.linalg.norm(position) * np.linalg.norm(previous_position)))
            # assign this rotation to the vector perpendicular to rotation plane
            rpy_inertial_rotation_vector = self._actor_orbital_plane_normal * rpy_inertial_rotation_angle
            # this rotation needs to be compensated in the rotation of the body frame, so it's attitude stays fixed
            self._actor_theta_1 += -eci_to_rpy(rpy_inertial_rotation_vector, position, velocity)

            # theta_2:
            # to not have the spacecraft rotate in the first timestep:
            if self._actor_t == 0:
                #self._actor_theta_2 = np.array([0.0, 0.0, 0.0])
                pass
            else:
                body_rotation = np.array(self._actor_angular_velocity) * dt
                # theta_2 = body_to_rpy(body_rotation, self._actor_attitude_in_rad) # this seems to break it
                self._actor_theta_2 += body_rotation

            # updated attitude
            self._actor_attitude_in_rad = self._actor_theta_1 + self._actor_theta_2

            # set values close to zero equal to zero.
            self._actor_attitude_in_rad[np.isclose(self._actor_attitude_in_rad, np.zeros(3))] = 0

            # attitude in range [-π, π]:
            self._actor_attitude_in_rad = np.arctan2(
                np.sin(self._actor_attitude_in_rad), np.cos(self._actor_attitude_in_rad))

            # pointing vector
            # todo: change function names to make sense
            # the following sequence of rotations is very important in order to make the model work
            # more insight into the transformation functions rotation sequences is needed to make sense of this
            # first rotate body pointing vector with theta 2:

            # body rotation in body frame
            pointing_vector = rodriguez_rotation(self._actor_pointing_vector_body, self._actor_theta_2)

            # secondly rotate body pointing vector with theta 1:

            # todo: figure out how this works:
            # pointing vector is rotated every step wrt beginning position, in the beginning body coincides with rpy,
            # thus rodriguez rotations happen in rpy frame, not body.
            
            # therefore the following actually rotates the body within rpy with theta 1:
            # pointing_vector = body_to_rpy(np.ndarray.tolist(pointing_vector), np.ndarray.tolist(self._actor_theta_1))
            # self._actor_pointing_vector_eci = rpy_to_eci(np.ndarray.tolist(pointing_vector), position, velocity)
            
            # body rotation in rpy frame
            pointing_vector = rodriguez_rotation(pointing_vector, self._actor_theta_1)
            self._actor_pointing_vector_eci = rpy_to_eci(np.ndarray.tolist(pointing_vector), position, velocity)

            # set values close to zero equal to zero.
            self._actor_pointing_vector_eci[np.isclose(self._actor_pointing_vector_eci, np.zeros(3))] = 0

            # convert to list
            self._actor_attitude_in_rad = np.ndarray.tolist(self._actor_attitude_in_rad)
            """
        # position
        position = self._actor.get_position(self._actor.local_time)

        # previous position (will be None at first timestep)
        previous_position = self._actor._previous_position
        # call previous position before velocity, as "get_position_velocity" sets previous position to current one
        # todo: velocity function starts previous position... when initializing pointing vector,
        #       looks like this means next line is not needed:
        # todo: find correct way of relating roll, pitch, yaw angles to a vector (to have initial attitude)
        if not previous_position:  # first timestep

            # velocity, called only to update previous position.
            velocity = self._actor.get_position_velocity(self._actor.local_time)[1]
            starting_position = position

        else:
            # step:
            step = self._actor_t

            # velocity
            velocity = self._actor.get_position_velocity(self._actor.local_time)[1]

            # orbital plane normal unit vector
            self._actor_orbital_plane_normal = (np.cross(position, velocity) /
                                                np.linalg.norm(np.cross(position, velocity)))

            # attitude change due to two rotations:

            # theta_1:
            # rotation angle: arccos( (p . p_previous) / (||p|| ||p_previous||) )
            rpy_frame_rotation_angle_in_eci = np.arccos(np.linalg.multi_dot([position, previous_position]) /
                                                        (np.linalg.norm(position) * np.linalg.norm(previous_position)))
            # assign this scalar rotation angle to the vector perpendicular to rotation plane
            rpy_frame_rotation_vector_in_eci = self._actor_orbital_plane_normal * rpy_frame_rotation_angle_in_eci
            # this rotation needs to be compensated in the rotation of the body frame, so it's attitude stays fixed
            self._actor_theta_1 = -eci_to_rpy(np.ndarray.tolist(rpy_frame_rotation_vector_in_eci), position, velocity)

            # theta_2:
            # to not have the spacecraft rotate in the first timestep:
            # self._actor_theta_2 = np.array([0.0, 0.0, 0.0])
            if self._actor_t != 0:
                body_rotation = np.array(self._actor_angular_velocity) * dt
                self._actor_theta_2 = body_to_rpy(body_rotation, self._actor_attitude_in_rad)
                #self._actor_theta_2 = body_rotation

            xb_rpy = body_to_rpy([1,0,0], self._actor_attitude_in_rad)
            yb_rpy = body_to_rpy([0,1,0], self._actor_attitude_in_rad)
            zb_rpy = body_to_rpy([0,0,1], self._actor_attitude_in_rad)
            #att = self._actor_attitude_in_rad
            #point_b = self._actor_pointing_vector_body
            # transform body pointing vector to RPY "fixed" frame
            pointing_vector_rpy = body_to_rpy(self._actor_pointing_vector_body, self._actor_attitude_in_rad)

            # rotate the body within the rpy frame with these angles
            xb_rpy, yb_rpy, zb_rpy, pointing_vector_rpy = (
                rotate_body_vectors(xb_rpy,
                                    yb_rpy,
                                    zb_rpy,
                                    pointing_vector_rpy,
                                    self._actor_theta_1)

            )

            new_theta_2 = rodriguez_rotation(self._actor_theta_2, self._actor_theta_1)

            xb_rpy, yb_rpy, zb_rpy, pointing_vector_rpy = (
                rotate_body_vectors(xb_rpy,
                                    yb_rpy,
                                    zb_rpy,
                                    pointing_vector_rpy,
                                    new_theta_2)
            )

            # update new attitude:
            self._actor_attitude_in_rad = np.ndarray.tolist(np.array(get_rpy_angles(xb_rpy, yb_rpy, zb_rpy)))


            # update pointing vector
            self._actor_pointing_vector_eci = rpy_to_eci(pointing_vector_rpy, position, velocity)


        self._actor_t += 1

