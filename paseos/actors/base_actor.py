from loguru import logger
import pykep as pk


class BaseActor:
    """This (abstract) class is the baseline implementation of an actor
    (e.g. spacecraft, ground station) in the simulation. The abstraction allows
    some actors to have e.g. limited power (spacecraft) and others not to.
    """

    # Orbital parameters of the actor, stored in a pykep planet object
    _orbital_parameters = None

    # Constraint for max bandwidth used when comms are available
    _max_bandwidth_kbps = None

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

    def is_in_line_of_sight(position):
        """Determines whether a position is in line of sight of this actor

        Args:
            position (np.array): vector of 3 coordinates in central body frame.

        Returns:
            bool: true if in line-of-sight.
        """
        raise NotImplementedError("Not yet implemented.")
