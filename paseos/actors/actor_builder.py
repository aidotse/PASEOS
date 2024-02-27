from typing import Callable, Any

import numpy as np
import pykep as pk
from dotmap import DotMap
from loguru import logger
from skyfield.api import wgs84

from paseos.geometric_model.geometric_model import GeometricModel
from .base_actor import BaseActor
from .ground_station_actor import GroundstationActor
from .spacecraft_actor import SpacecraftActor
from ..central_body.central_body import CentralBody
from ..communication.device_type import DeviceType
from ..communication.transmitter_model import TransmitterModel
from ..communication.receiver_model import ReceiverModel
from ..communication.link_model import LinkModel
from ..power.power_device_type import PowerDeviceType
from ..radiation.radiation_model import RadiationModel
from ..thermal.thermal_model import ThermalModel


class ActorBuilder:
    """This class is used to construct actors."""

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(ActorBuilder, cls).__new__(cls)
        else:
            logger.debug(
                "Tried to create another instance of ActorBuilder. Keeping original one..."
            )
        return cls.instance

    def __init__(self):
        logger.trace("Initializing ActorBuilder")

    @staticmethod
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

        logger.trace(f"Creating an actor blueprint with name {name}")

        return actor_type(name, epoch)

    @staticmethod
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
        assert -90 <= latitude <= 90, "Latitude is -90 <= lat <= 90"
        assert -180 <= longitude <= 180, "Longitude is -180 <= lat <= 180"
        assert 0 <= minimum_altitude_angle <= 90, "0 <= minimum_altitude_angle <= 90."
        actor._skyfield_position = wgs84.latlon(
            latitude_degrees=latitude,
            longitude_degrees=longitude,
            elevation_m=elevation,
        )
        actor._minimum_altitude_angle = minimum_altitude_angle

    @staticmethod
    def set_central_body(
        actor: SpacecraftActor,
        pykep_planet: pk.planet,
        mesh: tuple = None,
        radius: float = None,
        rotation_declination: float = None,
        rotation_right_ascension: float = None,
        rotation_period: float = None,
    ):
        """Define the central body of the actor. This is the body the actor is orbiting around.

        If a mesh is provided, it will be used to compute visibility and eclipse checks.
        Otherwise, a sphere with the provided radius will be used. One of the two has to be
        provided.

        Note the specification here will not affect the actor orbit.
        For that, use set_orbit, set_TLE or set_custom_orbit.

        Args:
            actor (SpacecraftActor): Actor to update.
            pykep_planet (pk.planet): Central body as a pykep planet in heliocentric frame.
            mesh (tuple): A tuple of vertices and triangles defining a mesh.
            radius (float): Radius of the central body in meters. Only used if no mesh is provided.
            rotation_declination (float): Declination of the rotation axis in degrees in the
            central body's inertial frame. Rotation at current actor local time is presumed to be 0.
            rotation_right_ascension (float): Right ascension of the rotation axis in degrees in
            the central body's inertial frame. Rotation at current actor local time is presumed
            to be 0.
            rotation_period (float): Rotation period in seconds. Rotation at current actor local
            time is presumed to be 0.
        """
        assert isinstance(
            actor, SpacecraftActor
        ), "Central body only supported for SpacecraftActors"

        # Fuzzy type check for pykep planet
        assert "pykep.planet" in str(type(pykep_planet)), "pykep_planet has to be a pykep planet."
        assert mesh is not None or radius is not None, "Either mesh or radius has to be provided."
        assert mesh is None or radius is None, "Either mesh or radius has to be provided, not both."

        # Check rotation parameters
        if rotation_declination is not None:
            assert (
                rotation_declination >= -90 and rotation_declination <= 90
            ), "Rotation declination has to be -90 <= dec <= 90"
        if rotation_right_ascension is not None:
            assert (
                rotation_right_ascension >= -180 and rotation_right_ascension <= 180
            ), "Rotation right ascension has to be -180 <= ra <= 180"
        if rotation_period is not None:
            assert rotation_period > 0, "Rotation period has to be > 0"

        # Check if rotation parameters are set
        if (
            rotation_period is not None
            or rotation_right_ascension is not None
            or rotation_declination is not None
        ):
            assert (
                rotation_right_ascension is not None
            ), "Rotation right ascension has to be set for rotation."
            assert (
                rotation_declination is not None
            ), "Rotation declination has to be set. for rotation."
            assert rotation_period is not None, "Rotation period has to be set for rotation."
            assert mesh is not None, "Radius cannot only be set for mesh-defined bodies."

        if mesh is not None:
            # Check mesh
            assert isinstance(mesh, tuple), "Mesh has to be a tuple."
            assert len(mesh) == 2, "Mesh has to be a tuple of length 2."
            assert isinstance(mesh[0], np.ndarray), "Mesh vertices have to be a numpy array."
            assert isinstance(mesh[1], np.ndarray), "Mesh triangles have to be a numpy array."
            assert len(mesh[0].shape) == 2, "Mesh vertices have to be a numpy array of shape (n,3)."
            assert (
                len(mesh[1].shape) == 2
            ), "Mesh triangles have to be a numpy array of shape (n,3)."

        # Check if pykep planet is either orbiting the sun or is the sunitself
        # by comparing mu values
        assert np.isclose(pykep_planet.mu_central_body, 1.32712440018e20) or np.isclose(
            pykep_planet.mu_self, 1.32712440018e20
        ), "Central body has to either be the sun or orbiting the sun."

        # Check if the actor already had a central body
        if actor.has_central_body:
            logger.warning(
                "The actor already had a central body. Only one central body is supported. "
                "Overriding old body."
            )

        # Set central body
        actor._central_body = CentralBody(
            planet=pykep_planet,
            initial_epoch=actor.local_time,
            mesh=mesh,
            encompassing_sphere_radius=radius,
            rotation_declination=rotation_declination,
            rotation_right_ascension=rotation_right_ascension,
            rotation_period=rotation_period,
        )

        logger.debug(f"Added central body {pykep_planet} to actor {actor}")

    @staticmethod
    def set_custom_orbit(actor: SpacecraftActor, propagator_func: Callable, epoch: pk.epoch):
        """Define the orbit of the actor using a custom propagator function.
        The custom function has to return position and velocity in meters
        and meters per second respectively. The function will be called with the
        current epoch as the only parameter.

        Args:
            actor (SpacecraftActor): Actor to update.
            propagator_func (Callable): Function to propagate the orbit.
            epoch (pk.epoch): Current epoch.
        """
        assert callable(propagator_func), "propagator_func has to be callable."
        assert isinstance(epoch, pk.epoch), "epoch has to be a pykep epoch."
        assert isinstance(actor, SpacecraftActor), "Orbit only supported for SpacecraftActors"
        assert actor._orbital_parameters is None, "Actor already has an orbit."
        assert np.isclose(
            actor.local_time.mjd2000, epoch.mjd2000
        ), "The initial epoch has to match actor's local time."
        actor._custom_orbit_propagator = propagator_func

        # Try evaluating position and velocity to check if the function works
        try:
            position, velocity = actor.get_position_velocity(epoch)
            assert len(position) == 3, "Position has to be list of 3 floats."
            assert all(
                [isinstance(val, float) for val in position]
            ), "Position has to be list of 3 floats."
            assert len(velocity) == 3, "Velocity has to be list of 3 floats."
            assert all(
                [isinstance(val, float) for val in velocity]
            ), "Velocity has to be list of 3 floats."
        except Exception as e:
            logger.error(f"Error evaluating custom orbit propagator function: {e}")
            raise RuntimeError("Error evaluating custom orbit propagator function.")

        logger.debug(f"Added custom orbit propagator to actor {actor}")

    @staticmethod
    def set_TLE(
        actor: SpacecraftActor,
        line1: str,
        line2: str,
    ):
        """Define the orbit of the actor using a TLE. For more information on TLEs see
        https://en.wikipedia.org/wiki/Two-line_element_set .

        TLEs can be obtained from https://www.space-track.org/ or
        https://celestrak.com/NORAD/elements/

        Args:
            actor (SpacecraftActor): Actor to update.
            line1 (str): First line of the TLE.
            line2 (str): Second line of the TLE.

        Raises:
            RuntimeError: If the TLE could not be read.
        """
        try:
            actor._orbital_parameters = pk.planet.tle(line1, line2)
            # TLE only works around Earth
            ActorBuilder.set_central_body(actor, pk.planet.jpl_lp("earth"), radius=6371000)
        except RuntimeError:
            logger.error("Error reading TLE \n", line1, "\n", line2)
            raise RuntimeError("Error reading TLE")

        logger.debug(f"Added TLE to actor {actor}")

    @staticmethod
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
            central_body (pk.planet): Central body around which the actor is orbiting as a pykep
            planet.
        """
        assert isinstance(actor, SpacecraftActor), "Orbit only supported for SpacecraftActors"

        ActorBuilder.set_central_body(actor, central_body, radius=central_body.radius)
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

    @staticmethod
    def set_position(actor: BaseActor, position: list):
        """Sets the actors position. Use this if you do *not* want the actor to have a keplerian
        orbit around a central body.

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

    @staticmethod
    def set_geometric_model(
        actor: SpacecraftActor, mass: float, vertices=None, faces=None, scale: float = 1
    ):
        """Define geometry of the spacecraft actor. This is done in the spacecraft body reference
        frame, and can be
        transformed to the inertial/PASEOS reference frame using the reference frane
        transformations in the attitude
        model. When used in the attitude model, the geometric model is in the body reference frame.

        Args:
            actor (SpacecraftActor): Actor to update.
            mass (float): Mass of the spacecraft in kg.
            vertices (list): List of all vertices of the mesh in terms of distance (in m) from
            origin of body frame.
                Coordinates of the corners of the object. If not selected, it will default to a
                cube that can be scaled.
                by the scale. Uses Trimesh to create the mesh from this and the list of faces.
            faces (list): List of the indexes of the vertices of a face. This builds the faces of
            the satellite by
                defining the three vertices to form a triangular face. For a cuboid each face is
                split into two
                triangles. Uses Trimesh to create the mesh from this and the list of vertices.
            scale (float): Parameter to scale the cuboid by, defaults to 1.
        """
        assert mass > 0, "Mass is > 0"

        actor._mass = mass
        geometric_model = GeometricModel(
            local_actor=actor,
            actor_mass=mass,
            vertices=vertices,
            faces=faces,
            scale=scale,
        )
        actor._mesh = geometric_model.set_mesh()
        actor._moment_of_inertia = geometric_model.find_moment_of_inertia

    @staticmethod
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

        # If solar panel, check if the actor has a central body
        # to check eclipse
        if power_device_type == PowerDeviceType.SolarPanel:
            assert actor.has_central_body, "Solar panels require a central body to check eclipse."

        # Check if the actor already had a power device
        if actor.has_power_model:
            logger.warning(
                "The actor already had a power device. Currently only one device is supported. "
                "Overriding old device."
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

    @staticmethod
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
            data_corruption_events_per_s (float): Single bit of data being corrupted, events per
            second,
            i.e. a Single Event Upset (SEU).
            restart_events_per_s (float): Device restart being triggered, events per second.
            failure_events_per_s (float): Complete device failure, events per second,
            i.e. a Single Event Latch-Up (SEL).
        """
        # check for spacecraft actor
        assert isinstance(
            actor, SpacecraftActor
        ), "Radiation models are only supported for SpacecraftActors"

        assert data_corruption_events_per_s >= 0, "data_corruption_events_per_s cannot be negative."
        assert restart_events_per_s >= 0, "restart_events_per_s cannot be negative."
        assert failure_events_per_s >= 0, "failure_events_per_s cannot be negative."

        actor._radiation_model = RadiationModel(
            data_corruption_events_per_s=data_corruption_events_per_s,
            restart_events_per_s=restart_events_per_s,
            failure_events_per_s=failure_events_per_s,
        )
        logger.debug(f"Added radiation model to actor {actor}.")

    @staticmethod
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
        available at http://imartinez.etsiae.upm.es/~isidoro/tc3/Spacecraft%20Thermal%20Modelling
        %20and%20Testing.pdf

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
            body_surface_temperature_in_K (float, optional): Central body surface temperature.
            Defaults to 288.
            body_emissivity (float, optional): Centrla body emissivity [0,1] in IR. Defaults to 0.6.
            body_reflectance (float, optional): Central body reflectance of sun light. Defaults
            to 0.3.
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
                "The actor already had a thermal model. Currently only one model is supported. "
                "Overriding old model."
            )

        assert actor_mass > 0, "Actor mass has to be positive."

        assert (
            0 <= power_consumption_to_heat_ratio and power_consumption_to_heat_ratio <= 1.0
        ), "Heat ratio has to be 0 to 1."

        logger.trace("Checking actor thermal values for sensibility.")
        assert 0 <= actor_initial_temperature_in_K, "Actor initial temperature cannot be below 0K."
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
        assert 0 <= body_surface_temperature_in_K, "Body surface temperature cannot be below 0K."
        assert 0 <= body_emissivity and body_emissivity <= 1.0, "Body emissivity has to be 0 to 1"
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

    @staticmethod
    def add_comm_link(
        transmitter_actor: BaseActor,
        transmitter_name: str,
        receiver_actor: BaseActor,
        receiver_name: str,
        link_name: str,
        frequency: float = None,
    ) -> None:
        """Adds a link to an actor, used with link budget modelling.
        Args:
            transmitter_actor (BaseActor): actor that the communication link will be
            added to.
            transmitter_name (str): the name of the transmitter device.
            receiver_actor (BaseActor): the receiving actor.
            receiver_name (str): the name of the receiver device.
            link_name (str): the name of the link.
            frequency (float, optional): the frequency of the radio link. Cannot be used for
            optical where wavelength of 1550 is required.
        """
        transmitter_model = transmitter_actor.get_transmitter(transmitter_name)
        receiver_model = receiver_actor.get_receiver(receiver_name)

        if frequency is not None:
            assert frequency > 0, "Frequency needs to be higher than 0 Hz."
        link = LinkModel(
            transmitter_actor=transmitter_actor,
            transmitter_model=transmitter_model,
            receiver_actor=receiver_actor,
            receiver_model=receiver_model,
            frequency=frequency,
        )
        transmitter_actor.add_comm_link(link_name, link)

    @staticmethod
    def add_comm_device(
        actor: BaseActor,
        device_name: str,
        bandwidth_in_kbps: float = 0,
        input_power: float = 0,
        power_efficiency: float = 0,
        antenna_efficiency: float = 0,
        antenna_diameter: float = None,
        antenna_gain: float = None,
        point_losses: float = 0,
        line_losses: float = 0,
        polarization_losses: float = 0,
        noise_temperature: float = 0,
        fwhm: float = None,
        device_type: DeviceType = None,
    ):
        """Creates a communication device. Can be used by just setting bandwidth_in_kbps,
        or can be used with link budget modelling.

        Args:
            actor (BaseActor): actor that the communication device will be added to.
            device_name (str): device_name of the communication device.
            bandwidth_in_kbps (float): device bandwidth in kbps.
            input_power (float): input power of this device.
            power_efficiency (float): power efficiency of the device, between 0 and 1.
            antenna_efficiency (float): efficiency of the antenna, between 0 and 1.
            antenna_diameter (float): diameter of the antenna, in m. Either set antenna_gain,
            antenna_diameter or fwhm (only for optical).
            antenna_gain (float): gain of the antenna, in dB. Either set antenna_gain,
            or antenna_diameter or fwhm (fwhm only for optical).
            point_losses(float): pointing losses, in dB.
            line_losses (float): line losses, in dB.
            polarization_losses (float): polarization_losses, in dB.
            noise_temperature (float): noise temperature, in K.
            fwhm (float): full width at half maximum, in rad.
            device_type (DeviceType): type of the device.
        """
        # If link budget modelling is used.
        if device_type is not None:
            assert input_power >= 0, "Input power needs to be higher than 0."
            assert 0 <= power_efficiency <= 1, "Power efficiency should be between 0 and 1."
            assert 0 <= antenna_efficiency <= 1, "Antenna efficiency should be between 0 and 1."
            assert line_losses >= 0, "Line losses needs to be 0 or higher."
            assert point_losses >= 0, "Pointing losses needs to be 0 or higher."
            assert line_losses >= 0, "Line losses needs to be 0 or higher."
            assert polarization_losses >= 0, "Polarization losses needs to be 0 or higher."
            assert noise_temperature >= 0, "Noise temperature needs to be 0 or higher."
            if fwhm is not None:
                assert fwhm >= 0, "full width at half maximum needs to be 0 or higher."
            if antenna_gain is not None:
                assert antenna_gain >= 0, "Antenna gain needs to be 0 or higher."
            if antenna_diameter is not None:
                assert antenna_diameter >= 0, "Antenna diameter needs to be 0 or higher"
            assert (
                antenna_gain is not None or antenna_diameter is not None or fwhm is not None
            ), "Antenna gain or antenna diameter or fwhm needs to be set."
            assert not (
                antenna_diameter is not None
                and antenna_gain is not None
                or antenna_diameter is not None
                and fwhm is not None
                or antenna_gain is not None
                and fwhm is not None
            ), "Only set one of antenna gain, antenna diameter and fwhm not multiple."

        if device_type == DeviceType.RADIO_TRANSMITTER:
            assert isinstance(
                actor, SpacecraftActor
            ), "Only a spacecraft can contain a radio transmitter."
            radio_transmitter = TransmitterModel(
                input_power=input_power,
                power_efficiency=power_efficiency,
                antenna_efficiency=antenna_efficiency,
                line_losses=line_losses,
                point_losses=point_losses,
                antenna_gain=antenna_gain,
                antenna_diameter=antenna_diameter,
                device_type=device_type,
            )
            actor.add_transmitter(device_name, radio_transmitter)
        elif device_type == DeviceType.RADIO_RECEIVER:
            radio_receiver = ReceiverModel(
                line_losses=line_losses,
                polarization_losses=polarization_losses,
                noise_temperature=noise_temperature,
                antenna_diameter=antenna_diameter,
                antenna_gain=antenna_gain,
                device_type=device_type,
            )
            actor.add_receiver(device_name, radio_receiver)
        elif device_type == DeviceType.OPTICAL_TRANSMITTER:
            assert isinstance(
                actor, SpacecraftActor
            ), "Only a spacecraft can contain an optical transmitter."
            optical_transmitter = TransmitterModel(
                input_power=input_power,
                power_efficiency=power_efficiency,
                antenna_efficiency=antenna_efficiency,
                line_losses=line_losses,
                point_losses=point_losses,
                antenna_gain=antenna_gain,
                antenna_diameter=antenna_diameter,
                fwhm=fwhm,
                device_type=device_type,
            )
            actor.add_transmitter(device_name, optical_transmitter)
        elif device_type == DeviceType.OPTICAL_RECEIVER:
            assert isinstance(
                actor, SpacecraftActor
            ), "Only a spacecraft can contain an optical receiver."
            optical_receiver = ReceiverModel(
                line_losses=line_losses,
                antenna_diameter=antenna_diameter,
                antenna_gain=antenna_gain,
                device_type=device_type,
            )
            actor.add_receiver(device_name, optical_receiver)
        else:
            if device_name in actor.communication_devices:
                raise ValueError(
                    "Trying to add already existing communication device with device_name: "
                    + device_name
                )
            actor._communication_devices[device_name] = DotMap(bandwidth_in_kbps=bandwidth_in_kbps)

            logger.debug(
                f"Added comm device with bandwidth={bandwidth_in_kbps} kbps to actor {actor}."
            )

    @staticmethod
    def add_custom_property(
        actor: BaseActor,
        property_name: str,
        initial_value: Any,
        update_function: Callable,
    ):
        """Adds a custom property to the actor. This e.g. allows tracking any physical
        the user would like to track.

        The update functions needs to take three parameters as input: the actor,
        the time to advance the state / model and the current_power_consumption_in_W
        and return the new value of the custom property.
        The function will be called with (actor,0,0) to check correctness.

        Args:
            actor (BaseActor): The actor to add the custom property to.
            property_name (str): The name of the custom property.
            initial_value (Any): The initial value of the custom property.
            update_function (Callable): The function to update the custom property.
        """
        if property_name in actor._custom_properties:
            raise ValueError(f"Custom property '{property_name}' already exists for actor {actor}.")

        # Already adding property but will remove if the update function fails
        actor._custom_properties[property_name] = initial_value

        # Check if the update function accepts the required parameters
        try:
            logger.trace(f"Checking update function for actor {actor} with time 0 and power 0.")
            new_value = update_function(actor, 0, 0)
            logger.debug(
                f"Update function returned {new_value} for actor {actor} with time 0 and power 0."
            )
        except TypeError as e:
            logger.error(e)
            # remove property if this failed
            del actor._custom_properties[property_name]
            raise TypeError(
                "Update function must accept three parameters: actor, time_to_advance, "
                "current_power_consumption_in_W."
            )

        # Check that the update function returns a value of the same type as the initial value
        if type(new_value) is not type(initial_value):
            # remove property if this failed
            del actor._custom_properties[property_name]
            raise TypeError(
                f"Update function must return a value of type {type(initial_value)} matching "
                f"initial vaue."
            )

        # Check that the initial value is the same as the value returned by the update function
        # with time 0
        if new_value != initial_value:
            # remove property if this failed
            del actor._custom_properties[property_name]
            raise ValueError(
                "Update function must return the existing value when called with unchanged time ("
                "dt = 0)."
            )

        actor._custom_properties_update_function[property_name] = update_function

        logger.debug(f"Added custom property '{property_name}' to actor {actor}.")
