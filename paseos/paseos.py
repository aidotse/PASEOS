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
    _known_actors = None

    # The actor of the device this is running on
    _local_actor = None

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
        self._known_actors = {}
        self._local_actor = local_actor
        self._activities = DotMap(_dynamic=False)

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

            # Perform updates for local actor (e.g. charging)
            # Each actor only updates itself
            # charge from current moment to time after timestep
            self._local_actor.charge(
                self._local_actor._local_time,
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

    def emtpy_known_actors(self):
        self._known_actors = {}

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
        if name in self._activities.keys():
            raise ValueError(
                "Trying to add already existing activity with name: "
                + name
                + ". Already have "
                + str(self._activities[name])
            )

        self._activities[name] = DotMap(
            requires_line_of_sight_to=requires_line_of_sight_to,
            power_consumption_in_watt=power_consumption_in_watt,
            _dynamic=False,
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
        # Check if activity exists and if it already had consumption specified
        assert name in self._activities.keys(), (
            "Activity not found. Declared activities are" + self._activities.keys()
        )
        activity = self._activities[name]

        if power_consumption_in_watt is None:
            power_consumption_in_watt = activity.power_consumption_in_watt

        assert power_consumption_in_watt > 0, (
            "Power consumption has to be positive but was either in activity or call specified as "
            + str(power_consumption_in_watt)
        )

        assert duration_in_s > 0, "Duration has to be positive."

        # TODO
        # Check if line of sight requirement is fulfilled and if enough power available
        assert (
            activity.requires_line_of_sight_to is None
        ), "Line of Sight for activities is not implemented"

        # TODO
        # Perform activity, maybe we allow the user pass a function to be executed?
        self._local_actor.discharge(power_consumption_in_watt, duration_in_s)

        return True

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
