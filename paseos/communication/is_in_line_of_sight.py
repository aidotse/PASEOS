from loguru import logger
import pykep as pk
import os
import numpy as np
from skspatial.objects import Line
from skyfield.units import AU_M
from skyfield.api import load
from skyfield.vectorlib import VectorFunction


_SKYFIELD_EARTH_PATH = os.path.join(
    os.path.dirname(__file__) + "/../resources/", "de421.bsp"
)
# Skyfield Earth, in the future we may not always want to load this.
_SKYFIELD_EARTH = load(_SKYFIELD_EARTH_PATH)["earth"]


class SkyfieldSkyCoordinate(VectorFunction):
    """Small helper class to compute altitude angle"""

    def __init__(self, r_in_m, earth_pos_in_au):
        # Value 0 corresponds to the solar system barycenter according to
        # this: https://rhodesmill.org/skyfield/api-vectors.html#skyfield.vectorlib.VectorFunction.center
        self.center = 0
        # Position vector
        self.r = earth_pos_in_au + r_in_m / AU_M

    @property
    def target(self):
        # This is a property to avoid circular references as described
        # here: https://github.com/skyfielders/python-skyfield/blob/master/skyfield/planetarylib.py#L222
        return self

    def _at(self, t):
        # Velocity vector
        v = [0.0, 0.0, 0.0]
        return self.r, v, self.center, "SkyfieldSkyCoordinate"


def _is_in_line_of_sight_spacecraft_to_spacecraft(
    actor, other_actor, epoch: pk.epoch, plot=False
):
    """Determines whether a position is in line of sight of this actor

    Args:
        actor (SpacecraftActor): The actors to check line of sight from
        other_actor (SpacecraftActor): The actor to check line of sight with
        epoch (pk,.epoch): Epoch at which to check the line of sight
        plot (bool): Whether to plot a diagram illustrating the positions.

    Returns:
        bool: true if in line-of-sight.
    """
    logger.debug(
        "Computing line of sight between actors: " + str(actor) + " " + str(other_actor)
    )
    my_pos, _ = actor.get_position_velocity(epoch)
    other_actor_pos, _ = other_actor.get_position_velocity(epoch)

    logger.trace(
        "Computed positions for actors are "
        + str(my_pos)
        + " and "
        + str(other_actor_pos)
    )
    line_between_actors = Line(
        my_pos,
        [
            other_actor_pos[0] - my_pos[0],
            other_actor_pos[1] - my_pos[1],
            other_actor_pos[2] - my_pos[2],
        ],
    )
    if plot:
        from skspatial.plotting import plot_3d

    # Currently skspatial throws a ValueError if there is no intersection so we have to use this rather ugly way.
    try:
        p1, p2 = actor._central_body_sphere.intersect_line(line_between_actors)
        logger.trace("Intersections observed at " + str(p1) + " and " + str(p2))
        if plot:
            plot_3d(
                line_between_actors.plotter(t_1=0, t_2=1, c="k"),
                actor._central_body_sphere.plotter(alpha=0.2),
                p1.plotter(c="r", s=100),
                p2.plotter(c="r", s=100),
            )
    except ValueError:
        if plot:
            plot_3d(
                line_between_actors.plotter(t_1=0, t_2=1, c="k"),
                actor._central_body_sphere.plotter(alpha=0.2),
            )
        return True
    return False


def _is_in_line_of_sight_ground_station_to_spacecraft(
    ground_station,
    spacecraft,
    epoch: pk.epoch,
    minimum_altitude_angle: float,
    plot=False,
):
    """Determines whether a position is in line of sight of this actor

    Args:
        ground_station (GroundstationActor): The actors to check line of sight from
        spacecraft (SpacecraftActor): The actor to check line of sight with
        epoch (pk,.epoch): Epoch at which to check the line of sight
        minimum_altitude_angle(float): The altitude angle (in degree) at which the actor
        has to be in relation to the ground station position to be visible.
        It has to be between 0 and 90. Only relevant if one of the actors is a ground station.
        plot (bool): Whether to plot a diagram illustrating the positions.

    Returns:
        bool: true if in line-of-sight.
    """
    assert (
        minimum_altitude_angle < 90 and minimum_altitude_angle > 0
    ), "0 < Minimum altitude angle < 90"

    logger.debug(
        "Computing line of sight between actors: "
        + str(ground_station)
        + " "
        + str(spacecraft)
    )

    # Converting time to skyfield to use its API
    t_skyfield = ground_station._skyfield_timescale.tt_jd(epoch.jd)

    # Ground station location in barycentric
    gs_position = (_SKYFIELD_EARTH + ground_station._skyfield_position).at(t_skyfield)

    # Actor position in barycentric
    other_actor_pos = SkyfieldSkyCoordinate(
        r_in_m=np.array(spacecraft.get_position(epoch)),
        earth_pos_in_au=_SKYFIELD_EARTH.at(t_skyfield).position.au,
    )

    # Trigger observation calculation
    observation = gs_position.observe(other_actor_pos).apparent()

    # Compute angle
    altitude_angle = observation.altaz()[0].degrees

    logger.debug("Computed angle was " + str(altitude_angle))

    # Plot if requested
    if plot:
        from skspatial.plotting import plot_3d
        from skspatial.objects import Sphere, Line, Point

        def plot(gs_pos_t, sat_pos_t, t):
            # Converting to geocentric
            r1 = gs_pos_t.position.m - _SKYFIELD_EARTH.at(t).position.m
            r2 = sat_pos_t.position.m - _SKYFIELD_EARTH.at(t).position.m
            gs_point = Point(r1)
            sat_point = Point(r2)
            line = Line(r1, r2 - r1)
            plot_3d(
                spacecraft._central_body_sphere.plotter(alpha=0.4),
                line.plotter(c="b"),
                gs_point.plotter(c="r", s=100),
                sat_point.plotter(c="r", s=100),
            )

        plot(gs_position, other_actor_pos.at(t_skyfield), t_skyfield)

    return altitude_angle > minimum_altitude_angle and altitude_angle < 90


def is_in_line_of_sight(
    actor,
    other_actor,
    epoch: pk.epoch,
    minimum_altitude_angle: float = None,
    plot=False,
):
    """Determines whether a position is in line of sight of this actor

    Args:
        actor (BaseActor): The actors to check line of sight from
        other_actor (BaseActor): The actor to check line of sight with
        epoch (pk,.epoch): Epoch at which to check the line of sight
        minimum_altitude_angle(float): The altitude angle (in degree) at which the actor
        has to be in relation to the surface, has to be between 0 and 90.
        to be visible from this ground station. Has to be > 0 and < 90.
        Only relevant if one of the actors is a ground station.
        plot (bool): Whether to plot a diagram illustrating the positions.

    Returns:
        bool: true if in line-of-sight.
    """

    # Can't import types given circular import then, thus check with names
    if (
        type(actor).__name__ == "SpacecraftActor"
        and type(other_actor).__name__ == "SpacecraftActor"
    ):
        assert (
            actor._central_body_sphere is not None
        ), f"Please set the central sphere on actor {actor} for line of sight computations."
        return _is_in_line_of_sight_spacecraft_to_spacecraft(
            actor, other_actor, epoch, plot
        )
    elif (
        type(actor).__name__ == "GroundstationActor"
        and type(other_actor).__name__ == "SpacecraftActor"
    ):
        if minimum_altitude_angle is None:
            minimum_altitude_angle = actor._minimum_altitude_angle
        assert (
            other_actor._central_body_sphere is not None
        ), f"Please set the central sphere on actor {other_actor} for line of sight computations."
        return _is_in_line_of_sight_ground_station_to_spacecraft(
            actor, other_actor, epoch, minimum_altitude_angle, plot
        )
    elif (
        type(actor).__name__ == "SpacecraftActor"
        and type(other_actor).__name__ == "GroundstationActor"
    ):
        if minimum_altitude_angle is None:
            minimum_altitude_angle = other_actor._minimum_altitude_angle
        assert (
            actor._central_body_sphere is not None
        ), f"Please set the central sphere on actor {actor} for line of sight computations."
        return _is_in_line_of_sight_ground_station_to_spacecraft(
            other_actor, actor, epoch, minimum_altitude_angle, plot
        )
    else:
        raise NotImplementedError(
            f"Cannot compute line of sight between {type(actor).__name__} and {type(other_actor).__name__}."
        )
