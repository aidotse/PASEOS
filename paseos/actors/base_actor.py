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

    # Timestep this actor's info is at (excl. pos/vel)
    _local_time = None

    # Orbital parameters of the actor, stored in a pykep planet object
    _orbital_parameters = None

    # Earth as a sphere (for now)
    # TODO replace this in the future depending on central body
    # Note that this needs to be specified in solar reference frame for now
    _central_body_sphere = Sphere([0, 0, 0], 6371000)

    # Central body this actor is orbiting
    _central_body = None

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
        BaseActor._check_init_value_sensibility(position, velocity)
        super().__init__()
        self.name = name
        self._local_time = epoch
        self._central_body = central_body
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

    @staticmethod
    def _check_init_value_sensibility(
        position,
        velocity,
    ):
        """A function to check user inputs for sensibility

        Args:
            position (list of floats): [x,y,z]
            velocity (list of floats): [vx,vy,vz]
        """
        logger.trace("Checking constructor values for sensibility.")
        assert len(position) == 3, "Position has to have 3 elements (x,y,z)"
        assert len(velocity) == 3, "Velocity has to have 3 elements (vx,vy,vz)"

    def __str__(self):
        return self._orbital_parameters.name

    def set_time(self, t: pk.epoch):
        """Updates the local time of the actor.

        Args:
            t (pk.epoch): Local time to set to.
        """
        self._local_time = t

    def charge(self, t0: pk.epoch, t1: pk.epoch):
        """Charges the actor during that period. Not implemented by default.

        Args:
            t0 (pk.epoch): Start of the charging interval
            t1 (pk.epoch): End of the charging interval

        """
        pass

    def discharge(self, consumption_rate_in_W: float, duration_in_s: float):
        """Discharge battery depending on power consumption. Not implemented by default.

        Args:
            consumption_rate_in_W (float): Consumption rate of the activity in Watt
            duration_in_s (float): How long the activity is performed in seconds
        """
        pass


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
