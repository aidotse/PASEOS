from dotmap import DotMap
from loguru import logger
import pykep as pk

from paseos.actors.base_actor import BaseActor

from .utils.load_default_cfg import load_default_cfg


class PASEOS:
    """This class serves as the main interface with the user. It is designed
    as a singleton to ensure we only have one instance running at any time."""

    # Config file of the simulation
    _cfg = None

    # Stores the simulation state
    _state = None

    # Storing actors as dictionary for easy access
    actors = None

    # Stores registered activities
    _activities = None

    def __new__(self):
        if not hasattr(self, "instance"):
            self.instance = super(PASEOS, self).__new__(self)
        else:
            logger.warning(
                "Tried to create another instance of PASEOS simulation.Keeping original one..."
            )
        return self.instance

    def __init__(self):
        logger.trace("Initializing PASEOS")
        self._cfg = load_default_cfg()
        self._state = DotMap(_dynamic=False)
        self._state.time = 0
        self.actors = {}
        self._activities = {}

    def advance_time(self, time_to_advance: float):
        """Advances the simulation by a specified amount of time

        Args:
            time_to_advance (float): Time to advance in seconds.
        """
        logger.debug("Advancing time by " + str(time_to_advance) + " s.")
        target_time = self._state.time + time_to_advance
        dt = self._cfg.sim.dt

        # Perform timesteps until target_time - dt reached,
        # then final smaller or equal timestep to reach target_time
        while self._state.time < target_time:
            for name, actor in self.actors.items():
                # TODO double check this modifies inplace
                actor.charge()

            if self._state.time > target_time - dt:
                # compute final timestep to catch up
                dt = self._state.time - target_time

            self._state.time += dt

        logger.debug("New time is: " + str(self._state.time) + " s.")

    def add_actor(self, actor: BaseActor):
        """Adds an actor to the simulation.

        Args:
            actor (BaseActor): Actor to add
        """
        logger.debug("Adding actor:" + str(actor))
        logger.debug("Current actors: " + str(self.actors.keys()))
        # Check for duplicate actors by name
        if actor.name in self.actors.keys():
            raise ValueError(
                "Trying to add actor with already existing name: " + actor.name
            )
        # Else add
        self.actors[actor.name] = actor

    def register_activity(
        self,
        name: str,
        requires_line_of_sight: bool,
        power_consumption_in_wattseconds=-1.0,
    ):
        """Registers an activity that can then be performed on any actor.

        Args:
            name (str): Name of the activity
            requires_line_of_sight (bool): Whether this requires line of sight to other node.
            power_consumption_in_wattseconds (float, optional): Power consumption of performing the activity. Defaults to -1.0.
        """
        # TODO Store activity
        raise NotImplementedError()

    def perform_activity(
        self, actor_name: str, name: str, power_consumption_in_wattseconds: float = None
    ):
        # Check if activity and actor exist and if it already had consumption specified
        # TODO
        # Check if line of sight requirement is fulfilled and if enough power available
        # TODO
        # Perform activity
        # TODO
        # Return success status
        # TODO
        raise NotImplementedError()

    def set_central_body(self, planet: pk.planet):
        """Sets the central body of the simulation for the orbit simulation

        Args:
            planet (pk.planet): The central body as a pykep planet
        """
        logger.debug("Setting central body to " + planet)
        self._state.central_body = planet

    def get_cfg(self) -> DotMap:
        """Returns the current cfg of the simulation

        Returns:
            DotMap: cfg
        """
        return self._cfg
