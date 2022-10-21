from loguru import logger
import pykep as pk

from .base_actor import BaseActor
from .spacecraft_actor import SpacecraftActor
from .ground_station_actor import GroundstationActor


class ActorBuilder:
    """This class is used to construct actors."""

    def __new__(self):
        if not hasattr(self, "instance"):
            self.instance = super(ActorBuilder, self).__new__(self)
        else:
            logger.debug(
                "Tried to create another instance of ActorBuilder. Keeping original one..."
            )
        return self.instance

    def __init__(self):
        logger.trace("Initializing ActorBuilder")

    def get_actor_scaffold(name: str, actor_type: object, position, epoch: pk.epoch):
        """Initiates an actor with minimal properties.

        Args:
            name (str): Name of the actor.
            actor_type (object): Type of the actor (e.g. SpacecraftActor)
            position (list of floats): Starting position of the actor [x,y,z]
            epoch (pykep.epoch): Epoch at this position

        Returns:
            Created actor
        """
        assert (
            actor_type != BaseActor
        ), "BaseActor cannot be initiated. Please use SpacecraftActor or GroundstationActor"
        assert (
            actor_type == SpacecraftActor or actor_type == GroundstationActor
        ), f"Unsupported actor_type {actor_type}, Please use SpacecraftActor or GroundstationActor."

        logger.trace(f"Creating an actor blueprint with name {name}")

        return actor_type(name, position, epoch)

    def set_orbit(
        self,
        actor: BaseActor,
        position,
        velocity,
        epoch: pk.epoch,
        central_body: pk.planet,
    ):
        # Add checks for sensibility of orbit

        self._central_body = central_body
        self._orbital_parameters = pk.planet.keplerian(
            epoch,
            position,
            velocity,
            central_body.mu_self,
            1.0,
            1.0,
            1.0,
            actor.name,
        )

    def set_power_devices(
        self,
        actor: SpacecraftActor,
        battery_level_in_Ws: float,
        max_battery_level_in_Ws: float,
        charging_rate_in_W: float,
    ):
        """Add a power device (battery + some charging mechanism (e.g. solar power)) to the actor.
        This will allow constraints related to power consumption.

        Args:
            actor (SpacecraftActor): The actor to add to.
            battery_level_in_Ws (float): Current battery level in Watt seconds / Joule
            max_battery_level_in_Ws (float): Maximum battery level in Watt seconds / Joule
            charging_rate_in_W (float): Charging rate of the battery in Watt
        """

        # check for spacecraft actor
        assert isinstance(
            actor, SpacecraftActor
        ), "Power devices are only supported for SpacecraftActors"

        logger.trace("Checking battery values for sensibility.")
        assert battery_level_in_Ws > 0, "Battery level must be non-negative"
        assert max_battery_level_in_Ws > 0, "Battery level must be non-negative"
        assert charging_rate_in_W > 0, "Battery level must be non-negative"

        actor._max_battery_level_in_Ws = max_battery_level_in_Ws
        actor._battery_level_in_Ws = battery_level_in_Ws
        actor._charging_rate_in_W = charging_rate_in_W
        logger.debug(
            f"Added power device. MaxBattery={max_battery_level_in_Ws}Ws, "
            + f"CurrBattery={battery_level_in_Ws}Ws, "
            + f"ChargingRate={charging_rate_in_W}W"
        )

    def add_comm_device(
        self, actor: BaseActor, device_name: str, bandwidth_in_kbps: float
    ):
        pass
