from loguru import logger
import pykep as pk

from skspatial.objects import Line, Sphere

from abc import ABC

from dotmap import DotMap
from ..communication.check_communication_link import check_communication_link


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

    # Communication links dictionary
    _communication_links = DotMap(_dynamic=False)

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
        self._communication_links = DotMap(_dynamic=False)

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

    def add_communication_links(self, name, bandwidth_in_kbps):
        """Creates a communication link.

        Args:
            name (str): name of the communication link.
            bandwidth_in_kbps (float): link bandwidth in kbps.
        """
        self._communication_links[name] = DotMap(bandwidth_in_kbps=bandwidth_in_kbps)

    def check_communication_link(
        self,
        local_actor_communication_link_name,
        actor,
        dt: float,
        t0: float,
        data_to_send_in_b: int,
        window_timeout_value_in_s=7200.0
    ):
        """Checks how much data can be transmitted over the communication link and the length of the communication link.

        Args:
            local_actor_communication_link_name (base_actor):  name of the local_actor's communication link to use.
            actor (base_actor): other actor.
            dt (float): simulation timestep [s].
            t0 (float): current simulation time [s].
            data_to_send_in_b (int): amount of data to transmit [b].
            window_timeout_value_in_s (float, optional): timeout value for estimating the communication window. Defaults to 7200.0.
        Returns:
            int: remaining amount of data to transmit [b].
            float: length of the remaining communication window [s].
        """
        return check_communication_link(
            self, local_actor_communication_link_name, actor, dt, t0, data_to_send_in_b, window_timeout_value_in_s
        )
