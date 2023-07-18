"""This file serves to collect functionality related to central bodies."""

from math import radians, pi

from loguru import logger
from pyquaternion import Quaternion
from skspatial.objects import Sphere, LineSegment, Line, Point
import pykep as pk
import numpy as np

from paseos.actors.spacecraft_actor import SpacecraftActor
from paseos.central_body.sphere_between_points import sphere_between_points
from paseos.central_body.mesh_between_points import mesh_between_points
from paseos.utils.reference_frame import ReferenceFrame


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
    _rotation_angular_velocity = None

    def __init__(
        self,
        planet: pk.planet,
        initial_epoch: pk.epoch,
        mesh: tuple = None,
        encompassing_sphere_radius: float = None,
        rotation_declination: float = None,
        rotation_right_ascension: float = None,
        rotation_period: float = None,
    ):
        """Initializes a central body

        Args:
            planet (pk.planet): The planet object from pykep.
            initial_epoch (pk.epoch): The initial epoch of the simulation (important rotation computation).
            mesh (tuple, optional): A tuple containing the vertices and faces of the mesh. Defaults to None.
            encompassing_sphere_radius (float, optional): The radius of the encompassing sphere. Defaults to None.
            rotation_declination (float, optional): The declination of the rotation axis. Defaults to None.
            rotation_right_ascension (float, optional): The right ascension of the rotation axis. Defaults to None.
            rotation_period (float, optional): The rotation period of the body. Defaults to None.
        """

        self._planet = planet
        self._initial_epoch = initial_epoch
        self._mesh = mesh
        if encompassing_sphere_radius is not None:
            self._encompassing_sphere = Sphere([0, 0, 0], encompassing_sphere_radius)
        if (
            rotation_declination is not None
            and rotation_right_ascension is not None
            and rotation_period is not None
        ):
            if mesh is None or encompassing_sphere_radius is not None:
                logger.warning(
                    "You provided rotation parameters but no mesh. This will result in a non-rotating body."
                )

            # Setup spin axis of the body
            # Rotate spin axis according to declination
            q_dec = Quaternion(axis=[1, 0, 0], angle=radians(rotation_declination))
            # Rotate spin axis accordining to right ascension
            q_ra = Quaternion(axis=[0, 0, 1], angle=radians(rotation_right_ascension))
            # Composite rotation of q1 then q2 expressed as standard multiplication
            q_axis = q_dec * q_ra
            self._rotation_axis = q_axis.rotate([0, 0, 1])
            self._rotation_angular_velocity = 2.0 * pi / rotation_period

    def blocks_sun(self, actor: SpacecraftActor, t: pk.epoch, plot=False) -> bool:
        """Checks whether the central body blocks the sun for the given actor.

        Args:
            actor (SpacecraftActor): The actor to check
            t (pk.epoch): Epoch at which to check
            plot (bool): Whether to plot a diagram illustrating the positions.

        Returns:
            bool: True if the central body blocks the sun
        """
        logger.debug(f"Checking whether {actor} is in eclipse at {t}.")

        # Compute central body position in solar reference frame
        r_central_body_heliocentric, _ = np.array(self._planet.eph(t))
        logger.trace("r_central_body_heliocentric is" + str(r_central_body_heliocentric))

        # Compute satellite / actor position in solar reference frame
        r_sat_central_body_frame = np.array(actor.get_position(t))
        logger.trace("r_sat_central_body_frame is" + str(r_sat_central_body_frame))
        r_sat_heliocentric = r_central_body_heliocentric + r_sat_central_body_frame
        logger.trace("r_sat_heliocentric is" + str(r_sat_heliocentric))

        return self.is_between_points(
            [0, 0, 0], r_sat_heliocentric, t, ReferenceFrame.Heliocentric, plot
        )

    def is_between_actors(
        self, actor_1: SpacecraftActor, actor_2: SpacecraftActor, t: pk.epoch, plot=False
    ) -> bool:
        """Checks whether the central body is between the two actors.

        Args:
            actor_1 (SpacecraftActor): First actor
            actor_2 (SpacecraftActor): Second actor
            t (pk.epoch): Epoch at which to check
            plot (bool): Whether to plot a diagram illustrating the positions.

        Returns:
            bool: True if the central body is between the two actors
        """
        logger.debug("Computing line of sight between actors: " + str(actor_1) + " " + str(actor_2))
        pos_1 = actor_1.get_position_velocity(t)
        pos_2 = actor_2.get_position_velocity(t)

        return self.is_between_points(pos_1[0], pos_2[0], t, plot)

    def is_between_points(
        self,
        point_1,
        point_2,
        t: pk.epoch,
        reference_frame: ReferenceFrame = ReferenceFrame.CentralBodyInertial,
        plot: bool = False,
    ) -> bool:
        """Checks whether the central body is between the two points.

        Args:
            point_1 (np.array): First point
            point_2 (np.array): Second point
            t (pk.epoch): Epoch at which to check
            reference_frame (ReferenceFrame, optional): Reference frame of the points. Defaults to ReferenceFrame.CentralBodyInertial.
            plot (bool): Whether to plot a diagram illustrating the positions.

        Returns:
            bool: True if the central body is between the two points
        """
        logger.debug("Computing line of sight between points: " + str(point_1) + " " + str(point_2))

        point_1 = np.array(point_1)
        point_2 = np.array(point_2)

        # Convert to CentralBodyInertial reference frame ()
        if reference_frame == ReferenceFrame.Heliocentric:
            point_1 = point_1 - np.array(self._planet.eph(t)[0])
            point_2 = point_2 - np.array(self._planet.eph(t)[0])

        if self._encompassing_sphere is not None:
            return sphere_between_points(
                point_1=point_1,
                point_2=point_2,
                sphere=self._encompassing_sphere,
                plot=plot,
            )
        elif self._mesh is not None:
            # Apply rotation if specified
            if self._rotation_axis is not None:
                # We rotate the points to the central body's rotated frame
                point_1 = self._apply_rotation(point=point_1, epoch=t)
                point_2 = self._apply_rotation(point=point_2, epoch=t)
            return mesh_between_points(
                point_1=point_1,
                point_2=point_2,
                mesh_vertices=self._mesh[0],
                mesh_triangles=self._mesh[1],
            )
        else:
            logger.error("No mesh or encompassing sphere provided. Cannot check visibility.")
            raise ValueError("No mesh or encompassing sphere provided. Cannot check visibility.")

    def _apply_rotation(self, point, epoch: pk.epoch):
        """Applies the inverse rotation of the central body to the given point. This way
        the point will be in the central body's rotated frame. Avoids having to rotate
        the central body's mesh.

        Args:
            point (np.array): Point to rotate
            epoch (pk.epoch): Epoch at which to rotate

        Returns:
            np.array: Rotated point
        """

        # Compute rotation angle
        angle = (
            (epoch.mjd2000 - self._initial_epoch.mjd2000)
            * pk.DAY2SEC
            * self._rotation_angular_velocity
            * -1.0  # Inverse rotation
        )

        # Rotate point
        q = Quaternion(axis=self._rotation_axis, angle=angle)
        return q.rotate(point)
