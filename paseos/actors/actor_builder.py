from loguru import logger
from dotmap import DotMap
import pykep as pk
from skyfield.api import wgs84

from .base_actor import BaseActor
from .spacecraft_actor import SpacecraftActor
from .ground_station_actor import GroundstationActor
from ..thermal.thermal_model import ThermalModel
from ..power.power_device_type import PowerDeviceType
from ..radiation.radiation_model import RadiationModel


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
        minimum_altitude_angle: float = 30,
    ):
        """Define the position of a ground station actor.

        Args:
            actor (GroundstationActor): Actor to update.
            latitude (float): Latitude of the ground station in degrees.
            longitude (float): Longitude of the ground station in degrees.
            elevation (float): A distance specifying elevation above (positive)
            or below (negative) the surface of the Earth
            ellipsoid specified by the WSG84 model in meters. Defaults to 0.
            minimum_altitude_angle (float): Minimum angle above the horizon that
            this station can communicate with.
        """
        assert latitude >= -90 and latitude <= 90, "Latitude is -90 <= lat <= 90"
        assert longitude >= -180 and longitude <= 180, "Longitude is -180 <= lat <= 180"
        assert (
            minimum_altitude_angle >= 0 and minimum_altitude_angle <= 90
        ), "0 <= minimum_altitude_angle <= 90."
        actor._skyfield_position = wgs84.latlon(
            latitude_degrees=latitude,
            longitude_degrees=longitude,
            elevation_m=elevation,
        )
        actor._minimum_altitude_angle = minimum_altitude_angle

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
        power_device_type: PowerDeviceType = PowerDeviceType.SolarPanel,
    ):
        """Add a power device (battery + some charging mechanism (e.g. solar power)) to the actor.
        This will allow constraints related to power consumption.

        Args:
            actor (SpacecraftActor): The actor to add to.
            battery_level_in_Ws (float): Current battery level in Watt seconds / Joule
            max_battery_level_in_Ws (float): Maximum battery level in Watt seconds / Joule
            charging_rate_in_W (float): Charging rate of the battery in Watt
            power_device_type (PowerDeviceType): Type of power device.
            Either "SolarPanel" or "RTG" at the moment. Defaults to SolarPanel.
        """

        # check for spacecraft actor
        assert isinstance(
            actor, SpacecraftActor
        ), "Power devices are only supported for SpacecraftActors"

        # Check if the actor already had a power device
        if actor.has_power_model:
            logger.warning(
                "The actor already had a power device. Currently only one device is supported. Overriding old device."
            )

        logger.trace("Checking battery values for sensibility.")
        assert battery_level_in_Ws > 0, "Battery level must be positive"
        assert max_battery_level_in_Ws > 0, "Battery level must be positive"
        assert charging_rate_in_W > 0, "Battery level must be positive"
        assert (
            power_device_type == PowerDeviceType.SolarPanel
            or power_device_type == PowerDeviceType.RTG
        ), "Only SolarPanel and RTG devices supported."

        actor._power_device_type = power_device_type
        actor._max_battery_level_in_Ws = max_battery_level_in_Ws
        actor._battery_level_in_Ws = battery_level_in_Ws
        actor._charging_rate_in_W = charging_rate_in_W
        logger.debug(
            f"Added {power_device_type} power device. MaxBattery={max_battery_level_in_Ws}Ws, "
            + f"CurrBattery={battery_level_in_Ws}Ws, "
            + f"ChargingRate={charging_rate_in_W}W to actor {actor}"
        )

    def set_radiation_model(
        actor: SpacecraftActor,
        data_corruption_events_per_s: float,
        restart_events_per_s: float,
        failure_events_per_s: float,
    ):
        """Enables the radiation model allowing data corruption, activities being
        interrupted by restarts and potentially critical device failures. Set any of the
        passed rates to 0 to disable that particular model.

        Args:
            actor (SpacecraftActor):  The actor to add to.
            data_corruption_events_per_s (float): Single bit of data being corrupted, events per second,
            i.e. a Single Event Upset (SEU).
            restart_events_per_s (float): Device restart being triggered, events per second.
            failure_events_per_s (float): Complete device failure, events per second, i.e. a Single Event Latch-Up (SEL).
        """
        # check for spacecraft actor
        assert isinstance(
            actor, SpacecraftActor
        ), "Radiation models are only supported for SpacecraftActors"

        assert (
            data_corruption_events_per_s >= 0
        ), "data_corruption_events_per_s cannot be negative."
        assert restart_events_per_s >= 0, "restart_events_per_s cannot be negative."
        assert failure_events_per_s >= 0, "failure_events_per_s cannot be negative."

        actor._radiation_model = RadiationModel(
            data_corruption_events_per_s=data_corruption_events_per_s,
            restart_events_per_s=restart_events_per_s,
            failure_events_per_s=failure_events_per_s,
        )
        logger.debug(f"Added radiation model to actor {actor}.")

    def set_thermal_model(
        actor: SpacecraftActor,
        actor_mass: float,
        actor_initial_temperature_in_K: float,
        actor_sun_absorptance: float,
        actor_infrared_absorptance: float,
        actor_sun_facing_area: float,
        actor_central_body_facing_area: float,
        actor_emissive_area: float,
        actor_thermal_capacity: float,
        body_solar_irradiance: float = 1360,
        body_surface_temperature_in_K: float = 288,
        body_emissivity: float = 0.6,
        body_reflectance: float = 0.3,
        power_consumption_to_heat_ratio: float = 0.5,
    ):
        """Add a thermal model to the actor to model temperature based on
        heat flux from sun, central body albedo, central body IR, actor IR
        emission and due to actor activities.
        For the moment, it is a slightly simplified version
        of the single node model from "Spacecraft Thermal Control" by Prof. Isidoro Martínez
        available at http://imartinez.etsiae.upm.es/~isidoro/tc3/Spacecraft%20Thermal%20Modelling%20and%20Testing.pdf

        Args:
            actor (SpacecraftActor): Actor to model.
            actor_mass (float): Actor's mass in kg.
            actor_initial_temperature_in_K (float): Actor's initial temperature in K.
            actor_sun_absorptance (float): Actor's absorptance ([0,1]) of solar light
            actor_infrared_absorptance (float): Actor's absportance ([0,1]) of IR.
            actor_sun_facing_area (float): Actor area facing the sun in m^2.
            actor_central_body_facing_area (float): Actor area facing central body in m^2.
            actor_emissive_area (float): Actor area emitting (radiating) heat.
            actor_thermal_capacity (float): Actor's thermal capacity in J / (kg * K).
            body_solar_irradiance (float, optional): Irradiance from the sun in W. Defaults to 1360.
            body_surface_temperature_in_K (float, optional): Central body surface temperature. Defaults to 288.
            body_emissivity (float, optional): Centrla body emissivity [0,1] in IR. Defaults to 0.6.
            body_reflectance (float, optional): Central body reflectance of sun light. Defaults to 0.3.
            power_consumption_to_heat_ratio (float, optional): Conversion ratio for activities.
            0 leads to know heat-up due to activity. Defaults to 0.5.
        """
        # check for spacecraft actor
        assert isinstance(
            actor, SpacecraftActor
        ), "Thermal models are only supported for SpacecraftActors"

        # Check if the actor already had a thermal model
        if actor.has_thermal_model:
            logger.warning(
                "The actor already had a thermal model. Currently only one model is supported. Overriding old model."
            )

        assert actor_mass > 0, "Actor mass has to be positive."

        assert (
            0 <= power_consumption_to_heat_ratio
            and power_consumption_to_heat_ratio <= 1.0
        ), "Heat ratio has to be 0 to 1."

        logger.trace("Checking actor thermal values for sensibility.")
        assert (
            0 <= actor_initial_temperature_in_K
        ), "Actor initial temperature cannot be below 0K."
        assert (
            0 <= actor_sun_absorptance and actor_sun_absorptance <= 1.0
        ), "Absorptance has to be 0 to 1."
        assert (
            0 <= actor_infrared_absorptance and actor_infrared_absorptance <= 1.0
        ), "Absorptance has to be 0 to 1."
        assert 0 < actor_sun_facing_area, "Sun-facing area has to be > 0."
        assert 0 < actor_central_body_facing_area, "Body-facing area has to be > 0."
        assert 0 < actor_emissive_area, "Actor emissive area has to be > 0."
        assert 0 < actor_thermal_capacity, "Thermal capacity has to be > 0"

        logger.trace("Checking body thermal values for sensibility.")
        assert 0 < body_solar_irradiance, "Solar irradiance has to be > 0."
        assert (
            0 <= body_surface_temperature_in_K
        ), "Body surface temperature cannot be below 0K."
        assert (
            0 <= body_emissivity and body_emissivity <= 1.0
        ), "Body emissivity has to be 0 to 1"
        assert (
            0 <= body_reflectance and body_reflectance <= 1.0
        ), "Body reflectance has to be 0 to 1"

        actor._mass = actor_mass
        actor._thermal_model = ThermalModel(
            local_actor=actor,
            actor_initial_temperature_in_K=actor_initial_temperature_in_K,
            actor_sun_absorptance=actor_sun_absorptance,
            actor_infrared_absorptance=actor_infrared_absorptance,
            actor_sun_facing_area=actor_sun_facing_area,
            actor_central_body_facing_area=actor_central_body_facing_area,
            actor_emissive_area=actor_emissive_area,
            actor_thermal_capacity=actor_thermal_capacity,
            body_solar_irradiance=body_solar_irradiance,
            body_surface_temperature_in_K=body_surface_temperature_in_K,
            body_emissivity=body_emissivity,
            body_reflectance=body_reflectance,
            power_consumption_to_heat_ratio=power_consumption_to_heat_ratio,
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
