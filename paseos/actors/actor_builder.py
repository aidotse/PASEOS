from loguru import logger
from dotmap import DotMap
import pykep as pk
from skyfield.api import wgs84

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

    def get_actor_scaffold(name: str, actor_type: object, epoch: pk.epoch):
        """Initiates an actor with minimal properties.

        Args:
            name (str): Name of the actor.
            actor_type (object): Type of the actor (e.g. SpacecraftActor)
            epoch (pykep.epoch): Current local time of the actor.

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

        return actor_type(name, epoch)

    def set_ground_station_location(
        actor: GroundstationActor,
        latitude: float,
        longitude: float,
        elevation: float = 0,
    ):
        """Define the position of a ground station actor.

        Args:
            actor (GroundstationActor): Actor to update.
            latitude (float): Latitude of the ground station in degrees.
            longitude (float): Longitude of the ground station in degrees.
            elevation (float): Elevation of the ground station in meters. Defaults to 0.
        """
        assert elevation >= 0, "Elevation has to be non-negative."
        assert latitude >= -180 and latitude <= 180, "Latitude is -180 <= lat <= 180"
        assert longitude >= -180 and longitude <= 180, "Longitude is -180 <= lat <= 180"
        actor._skyfield_position = wgs84.latlon(
            latitude_degrees=latitude,
            longitude_degrees=longitude,
            elevation_m=elevation,
        )

    def set_orbit(
        actor: SpacecraftActor,
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

        assert isinstance(
            actor, SpacecraftActor
        ), "Orbit only supported for SpacecraftActors"

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

    def set_position(actor: BaseActor, position: list):
        """Sets the actors position. Use this if you do not want the actor to have a keplerian orbit around a central body.

        Args:
            actor (BaseActor): Actor set the position on.
            position (list): [x,y,z] position for SpacecraftActor.
        """
        assert not isinstance(
            actor, GroundstationActor
        ), "Position changing not supported for GroundstationActors"

        assert len(position) == 3, "Position has to be list of 3 floats."
        assert all(
            [isinstance(val, float) for val in position]
        ), "Position has to be list of 3 floats."
        actor._position = position
        logger.debug(f"Setting position {position} on actor {actor}")

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
        """Creates a communication device.

        Args:
            device_name (str): device_name of the communication device.
            bandwidth_in_kbps (float): device bandwidth in kbps.
        """
        if device_name in actor.communication_devices:
            raise ValueError(
                "Trying to add already existing communication device with device_name: "
                + device_name
            )

        actor._communication_devices[device_name] = DotMap(
            bandwidth_in_kbps=bandwidth_in_kbps
        )

        logger.debug(
            f"Added comm device with bandwith={bandwidth_in_kbps} kbps to actor {actor}."
        )
