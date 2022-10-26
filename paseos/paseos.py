from dotmap import DotMap
from loguru import logger
import pykep as pk

from paseos.actors.base_actor import BaseActor
from paseos.activities.activity_manager import ActivityManager

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
    _known_actors = None

    # The actor of the device this is running on
    _local_actor = None

    # Handles registered activities
    _activity_manager = None

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
        self._known_actors = {}
        self._local_actor = local_actor
        self._activity_manager = ActivityManager()

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
            if self._state.time > target_time - dt:
                # compute final timestep to catch up
                dt = target_time - self._state.time
            logger.trace(f"Time {self._state.time}, advancing {dt}")

            # Perform updates for local actor (e.g. charging)
            # Each actor only updates itself
            # charge from current moment to time after timestep
            self._local_actor.charge(
                self._local_actor.local_time,
                pk.epoch((self._state.time + dt) * pk.SEC2DAY),
            )

            self._state.time += dt
            self._local_actor.set_time(pk.epoch(self._state.time * pk.SEC2DAY))

        logger.debug("New time is: " + str(self._state.time) + " s.")

    def add_known_actor(self, actor: BaseActor):
        """Adds an actor to the simulation.

        Args:
            actor (BaseActor): Actor to add
        """
        logger.debug("Adding actor:" + str(actor))
        logger.debug("Current actors: " + str(self._known_actors.keys()))
        # Check for duplicate actors by name
        if actor.name in self._known_actors.keys():
            raise ValueError(
                "Trying to add already existing actor with name: " + actor.name
            )
        # Else add
        self._known_actors[actor.name] = actor

    @property
    def local_actor(self) -> BaseActor:
        """Returns the local actor.

        Returns:
            BaseActor: Local actor
        """
        return self._local_actor

    @property
    def known_actors(self) -> dict:
        """Returns known actors.

        Returns:
            dict of BaseActor: Dictionary of the known actors.
        """
        return self._known_actors

    @property
    def known_actor_names(self) -> list:
        """Returns names of known actors.

        Returns:
            list: List of names of known actors.
        """
        return self._known_actors.keys()

    def emtpy_known_actors(self):
        """Clears the list of known actors."""
        self._known_actors = {}

    def remove_known_actor(self, actor_name: str):
        """Remove an actor from the list of known actors.

        Args:
            actor_name (str): name of the actor to remove.
        """
        assert (
            actor_name in self.known_actors
        ), f"Actor {actor_name} is not in known. Available are {self.known_actors.keys()}"
        del self._known_actors[actor_name]

    def register_activity(
        self,
        name: str,
        requires_line_of_sight_to: list = None,
        power_consumption_in_watt: float = None,
    ):
        """Registers an activity that can then be performed on the local actor.

        Args:
            name (str): Name of the activity
            requires_line_of_sight_to (list): List of strings with names of actors which need to be visible for this activity.
            power_consumption_in_watt (float, optional): Power consumption of performing
            the activity (per second). Defaults to None.
        """
        self._activity_manager.register_activity(
            name=name,
            requires_line_of_sight_to=requires_line_of_sight_to,
            power_consumption_in_watt=power_consumption_in_watt,
        )

    def perform_activity(
        self,
        name: str,
        power_consumption_in_watt: float = None,
        duration_in_s: float = 1.0,
    ):
        """Perform the activity and discharge battery accordingly

        Args:
            name (str): Name of the activity
            power_consumption_in_watt (float, optional): Power consumption of the
            activity in seconds if not specified. Defaults to None.
            duration_in_s (float, optional): Time to perform this activity. Defaults to 1.0.

        Returns:
            bool: Whether the activity was performed successfully.
        """
        return self._activity_manager.perform_activity(
            name=name,
            local_actor=self.local_actor,
            power_consumption_in_watt=power_consumption_in_watt,
            duration_in_s=duration_in_s,
        )

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
