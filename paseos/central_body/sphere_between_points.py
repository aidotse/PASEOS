from skspatial.objects import Sphere, LineSegment, Line, Point
from loguru import logger


def sphere_between_points(point_1, point_2, sphere: Sphere, plot=False) -> bool:
    """Determines whether a sphere is between two points.

    Args:
        point_1 (np.array): First point
        point_2 (np.array): Second point
        sphere (Sphere): Sphere to check
        plot (bool): Whether to plot a diagram illustrating the positions.

    Returns:
        bool: true if blocking line-of-sight.
    """
    # Compute line between points
    line_between_points = Line(
        point=point_1,
        direction=point_2 - point_1,
    )

    # Specify line segment to see if intersections are on this segment
    linesegment_between_points = LineSegment(
        point_1,
        point_2,
    )

    # Currently skspatial throws a ValueError if there is no intersection
    # so we have to use this rather ugly way.
    try:
        p1, p2 = sphere.intersect_line(line_between_points)
        logger.trace("Intersections observed at " + str(p1) + " and " + str(p2))
        if plot:
            from skspatial.plotting import plot_3d

            sat_point = Point(point_2)
            plot_3d(
                line_between_points.plotter(t_1=0, t_2=0.001, c="k"),
                sphere.plotter(alpha=0.4),
                sat_point.plotter(c="b", s=100),
                p1.plotter(c="r", s=100),
                p2.plotter(c="r", s=100),
            )
    except ValueError:
        logger.trace("No intersections observed.")
        if plot:
            from skspatial.plotting import plot_3d

            sat_point = Point(point_2)
            plot_3d(
                line_between_points.plotter(c="k"),
                sphere.plotter(alpha=0.4),
                sat_point.plotter(c="b", s=100),
            )
        # No intersection
        return False
    # Check that the computed intersection is actually on the linesegment not infinite line
    if linesegment_between_points.contains_point(p1):
        logger.trace(f"p1={p1} is on the line between the intersection points.")
        return True
    elif linesegment_between_points.contains_point(p2):
        logger.trace(f"p2={p2} is on the line between the intersection points.")
        return True
    else:
        return False
