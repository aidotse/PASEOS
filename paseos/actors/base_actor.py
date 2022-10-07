from loguru import logger
import pykep as pk

from skspatial.objects import Line, Sphere

from abc import ABC


class BaseActor(ABC):
    """This (abstract) class is the baseline implementation of an actor
    (e.g. spacecraft, ground station) in the simulation. The abstraction allows
    some actors to have e.g. limited power (spacecraft) and others not to.
    """

    # Actor name, has to be unique
    name = None

    # Orbital parameters of the actor, stored in a pykep planet object
    _orbital_parameters = None

    # Constraint for max bandwidth used when comms are available
    _max_bandwidth_kbps = None

    # Earth as a sphere (for now)
    # TODO replace this in the future depending on central body
    _central_body_sphere = Sphere([0, 0, 0], 6371000)

    def __init__(
        self, name: str, position, velocity, epoch: pk.epoch, central_body: pk.planet
    ) -> None:
        """Constructor for a base actor

        Args:
            name (str): Name of this actor
            position (list of floats): [x,y,z]
            velocity (list of floats): [vx,vy,vz]
            epoch (pykep.epoch): Epoch at this pos / velocity
            central_body (pk.planet): pykep central body
        """
        logger.trace("Instantiating Actor.")
        super().__init__()
        self.name = name
        self._orbital_parameters = pk.planet.keplerian(
            epoch,
            position,
            velocity,
            central_body.mu_self,
            1.0,
            1.0,
            1.0,
            name,
        )

    def __str__(self):
        return self._orbital_parameters.name

    def get_position_velocity(self, epoch: pk.epoch):
        logger.trace(
            "Computing "
            + self._orbital_parameters.name
            + " position / velocity at time "
            + str(epoch.mjd2000)
            + " (mjd2000)."
        )
        return self._orbital_parameters.eph(epoch)

    def is_in_line_of_sight(
        self, other_actor: "BaseActor", epoch: pk.epoch, plot=False
    ):
        """Determines whether a position is in line of sight of this actor

        Args:
            other_actor (BaseActor): The actor to check line of sight with
            epoch (pk,.epoch): Epoch at which to check the line of sight
            plot (bool): Whether to plot a diagram illustrating the positions.

        Returns:
            bool: true if in line-of-sight.
        """
        logger.debug(
            "Computing line of sight between actors: "
            + str(self)
            + " "
            + str(other_actor)
        )
        my_pos, _ = self.get_position_velocity(epoch)
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
        print(line_between_actors)
        if plot:
            from skspatial.plotting import plot_3d

        # Currently skspatial throws a ValueError if there is no intersection so we have to use this rather ugly way.
        try:
            p1, p2 = self._central_body_sphere.intersect_line(line_between_actors)
            logger.trace("Intersections observed at " + str(p1) + " and " + str(p2))
            if plot:
                plot_3d(
                    line_between_actors.plotter(t_1=0, t_2=1, c="k"),
                    self._central_body_sphere.plotter(alpha=0.2),
                    p1.plotter(c="r", s=100),
                    p2.plotter(c="r", s=100),
                )
        except ValueError:
            if plot:
                plot_3d(
                    line_between_actors.plotter(t_1=0, t_2=1, c="k"),
                    self._central_body_sphere.plotter(alpha=0.2),
                )
            return True
        return False
