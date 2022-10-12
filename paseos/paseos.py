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

    # Storing actors we know as dictionary for easy access
    # Does not include local actor.
    known_actors = None

    # The actor of the device this is running on
    local_actor = None

    # Stores registered activities
    _activities = None

    def __new__(self, local_actor: BaseActor):
        if not hasattr(self, "instance"):
            self.instance = super(PASEOS, self).__new__(self)
        else:
            logger.warning(
                "Tried to create another instance of PASEOS simulation.Keeping original one..."
            )
        return self.instance

    def __init__(self, local_actor: BaseActor):
        logger.trace("Initializing PASEOS")
        self._cfg = load_default_cfg()
        self._state = DotMap(_dynamic=False)
        self._state.time = self._cfg.sim.start_time
        self.known_actors = {}
        self.local_actor = local_actor
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
            # Perform updates for local actor (e.g. charging)
            # Each actor only updates itself
            self.local_actor.charge()

            if self._state.time > target_time - dt:
                # compute final timestep to catch up
                dt = self._state.time - target_time

            self._state.time += dt
            self.local_actor.set_time(pk.epoch(self._state.time * pk.SEC2DAY))

        logger.debug("New time is: " + str(self._state.time) + " s.")

    def add_known_actor(self, actor: BaseActor):
        """Adds an actor to the simulation.

        Args:
            actor (BaseActor): Actor to add
        """
        logger.debug("Adding actor:" + str(actor))
        logger.debug("Current actors: " + str(self.known_actors.keys()))
        # Check for duplicate actors by name
        if actor.name in self.known_actors.keys():
            raise ValueError(
                "Trying to add already existing actor with name: " + actor.name
            )
        # Else add
        self.known_actors[actor.name] = actor

    def emtpy_known_actors(self):
        self.known_actors = {}

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
