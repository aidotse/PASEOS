from loguru import logger
import pykep as pk
import numpy as np


class AttitudeModel:


    _actor = None
    _actor_attitude_in_rad = None
    def __init__(
            self,
            local_actor,
            actor_initial_attitude_in_rad: list[float] = [0, 0, 0],
            ## add args with default value = None, if
            # actor_dipole
            # actor_drag_coefficient
            # body_J2
            #
    ):
        self._actor = local_actor
        self._actor_attitude_in_rad = actor_initial_attitude_in_rad

    def nadir_vector(self):
        """computes unit vector pointing towards earth, inertial body frame

        Returns:
            np array ([x, y, z]): unit nadir vector in ECIF (Earth-centered inertial frame)
        """
        u = np.array(self._actor.get_position)
        return -u/np.linalg.norm(u)

    def update_attitude(self, dt):
        """

        Args:
            dt (float): How far to advance the attitude computation.

        Returns:
            np array
        """
        # out: new euler angles
        #T = self._actor.get_disturbance