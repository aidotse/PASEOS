from loguru import logger
from dotmap import DotMap
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
        actor: BaseActor,
        position,
        velocity,
        epoch: pk.epoch,
        central_body: pk.planet,
    ):
        """Define the orbit of the actor

        Args:
            actor (BaseActor): The actor to define on
            position (list of floats): [x,y,z].
            velocity (list of floats): [vx,vy,vz].
            epoch (pk.epoch): Time of position / velocity.
            central_body (pk.planet): Central body around which the actor is orbiting as a pykep planet.
        """
        # TODO Add checks for sensibility of orbit

        actor._central_body = central_body
        actor._orbital_parameters = pk.planet.keplerian(
            epoch,
            position,
            velocity,
            central_body.mu_self,
            1.0,
            1.0,
            1.0,
            actor.name,
        )

        logger.debug(f"Added orbit to actor {actor}")

    def set_power_devices(
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
            + f"ChargingRate={charging_rate_in_W}W to actor {actor}"
        )

    def add_comm_device(actor: BaseActor, device_name: str, bandwidth_in_kbps: float):
        """Creates a communication link.

        Args:
            device_name (str): device_name of the communication device.
            bandwidth_in_kbps (float): link bandwidth in kbps.
        """
        if device_name in actor._communication_devices:
            raise ValueError(
                "Trying to add already existing communication link with device_name: "
                + device_name
            )

        actor._communication_devices[device_name] = DotMap(
            bandwidth_in_kbps=bandwidth_in_kbps
        )

        logger.debug(
            f"Added comm device with bandwith={bandwidth_in_kbps} kbps to actor {actor}."
        )
