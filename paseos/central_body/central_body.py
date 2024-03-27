"""This file serves to collect functionality related to central bodies."""

from math import radians, pi

from loguru import logger
from pyquaternion import Quaternion
from skspatial.objects import Sphere
from skyfield.api import wgs84, load

import pykep as pk
import numpy as np

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

            # Convert to rad
            rotation_declination = radians(rotation_declination)
            rotation_right_ascension = radians(rotation_right_ascension)
            # Define the rotation axis as a unit vector
            self._rotation_axis = np.array(
                [
                    np.cos(rotation_declination) * np.cos(rotation_right_ascension),
                    np.cos(rotation_declination) * np.sin(rotation_right_ascension),
                    np.sin(rotation_declination),
                ]
            )

            self._rotation_angular_velocity = 2.0 * pi / rotation_period

    @property
    def planet(self):
        return self._planet

    def blocks_sun(self, actor, t: pk.epoch, plot=False) -> bool:
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

    def is_between_actors(self, actor_1, actor_2, t: pk.epoch, plot=False) -> bool:
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
            reference_frame (ReferenceFrame, optional): Reference frame of the points.
            Defaults to ReferenceFrame.CentralBodyInertial.
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

    def magnetic_dipole_moment(
        self,
        epoch: pk.epoch,
        strength_in_Am2=7.79e22,
        pole_latitude_in_deg=79.6,
        pole_longitude_in_deg=-71.6,
    ):
        """Returns the time-dependent magnetic dipole moment vector of central body.
        Default values are for Earth. Earth dipole moment vector determined from the northern geomagnetic pole position
        using skyfield api, and actor epoch. To model the simplified Earth magnetic field as a magnetic dipole with an
        offset from the Earth rotational axis, at a specific point in time.

        Earth geomagnetic pole position and dipole moment strength values from the year 2000:
        Latitude: 79.6° N
        Longitude: 71.6° W
        Dipole moment: 7.79 x 10²² Am²
        https://wdc.kugi.kyoto-u.ac.jp/poles/polesexp.html

        (The same method used as ground station actor position determination)

        Args:
            epoch (pk.epoch): Epoch at which to get the dipole
            strength_in_Am2 (float): dipole strength in Am². Defaults to 7.79e22
            pole_latitude_in_deg (float): latitude of the Northern geomagnetic pole in degrees. Defaults to 79.6
            pole_longitude_in_deg (float): longitude of the Northern geomagnetic pole in degrees. Defaults to -71.6

        Returns: Time-dependent dipole moment vector in inertial frame (np.ndarray): [mx, my, mz]
        """
        if self.planet.name == "earth":
            # Converting time to skyfield to use its API
            t_skyfield = load.timescale().tt_jd(epoch.jd)

            # North geomagnetic pole location on Earth surface in cartesian coordinates
            dipole_north_direction = np.array(
                wgs84.latlon(pole_latitude_in_deg, pole_longitude_in_deg).at(t_skyfield).position.m
            )
            # Multiply geomagnetic pole position unit vector with dipole moment strength
            magnetic_dipole_moment = -(
                dipole_north_direction / np.linalg.norm(dipole_north_direction) * strength_in_Am2
            )
        else:
            # TODO add other planets' magnetic fields
            raise NotImplementedError("Magnetic dipole moment only modeled for Earth.")
            # For now: assume alignment with rotation axis
            magnetic_dipole_moment = np.array([0, 0, 1]) * strength_in_Am2

        return magnetic_dipole_moment
