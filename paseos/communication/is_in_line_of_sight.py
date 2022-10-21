from loguru import logger
import pykep as pk
from skspatial.objects import Line


def is_in_line_of_sight(actor, other_actor, epoch: pk.epoch, plot=False):
    """Determines whether a position is in line of sight of this actor

    Args:
        actor (BaseActor): The actors to check line of sight from
        other_actor (BaseActor): The actor to check line of sight with
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
