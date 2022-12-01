from loguru import logger
import pykep as pk
import numpy as np
from skyfield.api import load
from skyfield.units import AU_M

from paseos.actors.base_actor import BaseActor

from skyfield.vectorlib import VectorFunction


class SkyfieldSkyCoordinate(VectorFunction):
    """Small helper class to compute altitude angle"""

    def __init__(self, r_in_m, earth_pos_in_au):
        # Value 0 corresponds to the solar system barycenter according to this: https://rhodesmill.org/skyfield/api-vectors.html#skyfield.vectorlib.VectorFunction.center
        self.center = 0
        # Position vector
        self.r = earth_pos_in_au + r_in_m / AU_M

    @property
    def target(self):
        # This is a property to avoid circular references as described here: https://github.com/skyfielders/python-skyfield/blob/master/skyfield/planetarylib.py#L222
        return self

    def _at(self, t):
        # Velocity vector
        v = [0.0, 0.0, 0.0]
        return self.r, v, self.center, "SkyfieldSkyCoordinate"


class GroundstationActor(BaseActor):
    """This class models a groundstation actor."""

    # Ground station latitude / longitude
    _skyfield_position = None

    # Timescale object to convert from pykep epoch to skyfield time
    _skyfield_timescale = load.timescale()

    # Skyfield Earth position
    _skyfield_earth = load("de421.bsp")["earth"]

    def __init__(
        self,
        name: str,
        epoch: pk.epoch,
    ) -> None:
        """Constructor for a groundstation actor.

        Args:
            name (str): Name of this actor
            epoch (pykep.epoch): Epoch at this pos / velocity
        """
        logger.trace("Instantiating GroundstationActor.")
        super().__init__(name, epoch)

    def get_position(self, epoch: pk.epoch):
        """Compute the position of this ground station at a specific time.

        Args:
            epoch (pk.epoch): Time as pykep epoch

        Returns:
            np.array: [x,y,z] in meters
        """
        # Converting time to skyfield to use its API
        t_skyfield = self._skyfield_timescale.tt_jd(epoch.jd)

        # Getting ground station position, skyfield operates in GCRF frame
        # which is technically more precise than the J2000 we use but we neglect this here
        gcrf_position = self._skyfield_position.at(t_skyfield).position.m

        return gcrf_position

    def is_in_line_of_sight(
        self,
        other_actor: "BaseActor",
        epoch: pk.epoch,
        minimal_altitude: float,
        plot=False,
    ):
        """Determines whether a position is in line of sight of this ground station.

        Args:
            other_actor (BaseActor): The actor to check line of sight with
            epoch (pk,.epoch): Epoch at which to check the line of sight
            minimal_altitude(float): The altitude angle (in degree) at which the actor has to be in relation to the surface, has to be between 0 and 90.
            to be visible from this ground station. Has to be
            plot (bool): Whether to plot a diagram illustrating the positions.

        Returns:
            bool: true if in line-of-sight.
        """
        assert (
            minimal_altitude < 90 and minimal_altitude > 0
        ), "0 < Minimal altitude < 90"

        # Converting time to skyfield to use its API
        t_skyfield = self._skyfield_timescale.tt_jd(epoch.jd)

        # Ground station location in barycentric
        gs_position = (self._skyfield_earth + self._skyfield_position).at(t_skyfield)

        # Actor position in barycentric
        other_actor_pos = SkyfieldSkyCoordinate(
            r_in_m=np.array(other_actor.get_position(epoch)),
            earth_pos_in_au=self._skyfield_earth.position.au,
        )

        # Trigger observation calculation
        observation = gs_position.observe(other_actor_pos).apparent()

        # Compute angle
        altitude_angle = observation.altaz()[0].degrees

        # Plot if requested
        if plot:
            from skspatial.plotting import plot_3d
            from skspatial.objects import Sphere, Line, Point, LineSegment

            central_body_sphere = Sphere([0, 0, 0], 6371000)

            def plot(gs_pos_t, sat_pos_t, t):
                # Converting to geocentric
                r1 = gs_pos_t.position.m - self._skyfield_earth.at(t).position.m
                r2 = sat_pos_t.position.m - self._skyfield_earth.at(t).position.m
                gs_point = Point(r1)
                sat_point = Point(r2)
                line = Line(r1, r2 - r1)
                plot_3d(
                    central_body_sphere.plotter(alpha=0.4),
                    line.plotter(c="b"),
                    gs_point.plotter(c="r", s=100),
                    sat_point.plotter(c="r", s=100),
                )

            plot(gs_position, other_actor_pos.at(t_skyfield), t_skyfield)

        return altitude_angle > minimal_altitude and altitude_angle < 90
