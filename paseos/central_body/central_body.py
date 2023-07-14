"""This file serves to collect functionality related to central bodies."""

# For computing rotations of orbits
from pyquaternion import Quaternion


class CentralBody:
    """Class representing a central body. This can be the Earth
    but also any other user-defined body in the solar system."""

    # A mesh of the body, used for visibility checks if provided
    _mesh = None

    # A sphere encompassing the body, used for visibility checks if provided
    # and no mesh is provided
    _encompassing_sphere = None

    # The planet object from pykep, will be used to compute
    # heliocentric positions
    _planet = None

    # Rotation parameters (optional)
    _rotation_axis = None
    _rotation_period = None

    def intersect(self, point_1, point_2):
        """Returns whether the line between point_1 and point_2
        intersects the central body.

        Args:
            point_1 (list): Position of the first point
            point_2 (list): Position of the second point

        Returns:
            bool: True if the line intersects the central body
        """

        if self._mesh is not None:
            raise NotImplementedError()  # TODO
        elif self._encompassing_sphere is not None:
            raise NotImplementedError()  # TODO
        else:
            raise NotImplementedError("No mesh or encompassing sphere provided for central body.")
