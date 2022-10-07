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
        self._state.actors = []

    def advance_time(self, dt: float):
        """Advances the simulation by a specified amount of time

        Args:
            dt (float): Time to advance in seconds
        """
        logger.debug("Advancing time by " + str(dt) + " s.")
        self._state.time += dt

        logger.debug("New time is: " + str(self._state.time) + " s.")

    def add_actor(self, actor: BaseActor):
        """Adds an actor to the simulation.

        Args:
            actor (BaseActor): Actor to add
        """
        logger.debug("Adding actor:" + str(actor))
        # Check for duplicate actors by name
        for existing_actor in self._state.actors:
            if existing_actor.name == actor.name:
                raise ValueError(
                    "Trying to add actor with already existing name: " + actor.name
                )
        # Else add
        self._state.actors.append(actor)

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
