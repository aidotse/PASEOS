from loguru import logger

from abc import ABC


class BaseActor(ABC):
    """This (abstract) class is the baseline implementation of an actor
    (e.g. spacecraft, ground station) in the simulation. The abstraction allows
    some actors to have e.g. limited power (spacecraft) and others not to.
    """

    # Orbital parameters of the actor, described as position,
    # velocity vectors, ground stations are in "ground" orbit
    _position = None
    _velocity = None

    # Constraint for max bandwidth used when comms are available
    _max_bandwidth_kbps = None

    def __init__(self) -> None:
        logger.trace("Instantiating Actor.")
        super().__init__()

    def is_in_line_of_sight(position):
        """Determines whether a position is in line of sight of this actor

        Args:
            position (np.array): vector of 3 coordinates in central body frame.

        Returns:
            bool: true if in line-of-sight.
        """
        raise NotImplementedError("Not yet implemented.")
