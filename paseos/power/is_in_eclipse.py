"""This file provides method for computing whether an actor is currently in eclipse"""
import pykep as pk
import numpy as np
from skspatial.objects import LineSegment, Line, Sphere
from loguru import logger


def is_in_eclipse(
    actor,
    central_body: pk.planet,
    t: pk.epoch,
    plot=False,
) -> bool:
    """Checks whether the actor is currently in eclipse of central body.

    Args:
        actor: Actor to check
        central_body (pk.planet): Central body of the actor
        t (pk.epoch): Current time to check at
        plot (bool, optional): If true will plot visualization. Defaults to False.

    Returns:
        bool: True if actor is in eclipse
    """
    # on OSX this can throw an error it seems.
    try:
        logger.debug(f"Checking whether {actor} is in eclipse at {t}.")
    except RuntimeError:
        logger.debug(f"Checking whether {actor} is in eclipse at {t.mjd2000} (mjd2000).")

    # Compute central body position in solar reference frame
    r_central_body_heliocentric, _ = np.array(central_body.eph(t))
    logger.trace("r_central_body_heliocentric is" + str(r_central_body_heliocentric))
    central_body_sphere = Sphere(r_central_body_heliocentric, actor._central_body_sphere.radius)

    # Compute satellite / actor position in solar reference frame
    r_sat_central_body_frame = np.array(actor.get_position(t))
    logger.trace("r_sat_central_body_frame is" + str(r_sat_central_body_frame))
    r_sat_heliocentric = r_central_body_heliocentric + r_sat_central_body_frame
    logger.trace("r_sat_heliocentric is" + str(r_sat_heliocentric))

    # Compute line between actor and sun
    line_between_sun_and_actor = Line(
        [0, 0, 0],
        r_sat_heliocentric,
    )

    # Specify line segment to see if intersections are on this segment
    linesegment_between_sun_and_actor = LineSegment(
        [0, 0, 0],
        r_sat_heliocentric,
    )

    if plot:
        from skspatial.plotting import plot_3d
        from skspatial.objects import Point

    # Currently skspatial throws a ValueError if there is no intersection so we have to use this rather ugly way.
    try:
        p1, p2 = central_body_sphere.intersect_line(line_between_sun_and_actor)
        logger.trace("Intersections observed at " + str(p1) + " and " + str(p2))
        if plot:
            sat_point = Point(r_sat_heliocentric)
            plot_3d(
                line_between_sun_and_actor.plotter(t_1=0, t_2=0.001, c="k"),
                central_body_sphere.plotter(alpha=0.4),
                sat_point.plotter(c="b", s=100),
                p1.plotter(c="r", s=100),
                p2.plotter(c="r", s=100),
            )
    except ValueError:
        if plot:
            sat_point = Point(r_sat_heliocentric)
            plot_3d(
                line_between_sun_and_actor.plotter(c="k"),
                central_body_sphere.plotter(alpha=0.4),
                sat_point.plotter(c="b", s=100),
            )
        # No intersection, no eclipse
        return False
    # Check that the computed intersection is actually on the linesegment not infinite line
    if linesegment_between_sun_and_actor.contains_point(p1):
        logger.trace(f"p1={p1} is on the line between Sun and actor.")
        return True
    elif linesegment_between_sun_and_actor.contains_point(p2):
        logger.trace(f"p2={p2} is on the line between Sun and actor.")
        return True
    else:
        return False
