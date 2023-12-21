from loguru import logger
import numpy as np

class GeometricModel:
    """This model describes the geometry of the spacecraft
    Currently it assumes the spacecraft to be a cuboid shape, with width, length and height """

    _actor = None
    _actor_mass = None
    _actor_height = None
    _actor_length = None
    _actor_width = None

    def __init__(
            self,
            local_actor,
            actor_mass,
            actor_height,
            actor_length,
            actor_width
    ) -> None:
        """Describes the geometry of the spacecraft, and outputs relevant parameters related to the spacecraft body.
        Width is the size on the x-direction, Length in the y-direction, and height in the z-direction.

        Args:
            actor (SpacecraftActor): Actor to model.
            actor_mass (float): Actor's mass in kg.
            actor_height: Actor's size in the z-direction.
            actor_length: Actor's size in the y-direction.
            actor_width: Actor's size in the x-direction.
        """
        logger.trace("Initializing geometrical model.")

        self._actor = local_actor
        self._actor_mass = actor_mass
        self._actor_height = actor_height
        self._actor_length = actor_length
        self._actor_width = actor_width

    @property
    def _find_moi(self):
        """Actor moment of inertia, currently only suitable for a rectangular prism

        Returns:
            np.array: Mass moments of inertia for the actor

        I in the form of [[Ixx Ixy Ixz]
                          [Iyx Iyy Iyx]
                          [Izx Izy Izz]]
        """
        Ixx = self._actor_mass * (self._actor_height ** 2 + self._actor_length ** 2) / 12
        Iyy = self._actor_mass * (self._actor_height ** 2 + self._actor_width ** 2) / 12
        Izz = self._actor_mass * (self._actor_width ** 2 + self._actor_length ** 2) / 12
        # assume uniform mass distribution, hence Ixy, etc. are all zero
        self._actor_I = np.array([[Ixx, 0, 0],
                      [0, Iyy, 0],
                      [0, 0, Izz]])
        return self._actor_I

    # potentially add later for disturbances
    # def _find_cp(self):
    # def _find_dipole(self):