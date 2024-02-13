import numpy as np
import pykep as pk
from loguru import logger

from paseos.actors.base_actor import BaseActor
from paseos.power import discharge_model
from paseos.power import charge_model


class SpacecraftActor(BaseActor):
    """This class models a spacecraft actor which in addition to pos,
    velocity also has additional constraints such as power/battery."""

    # Power-related properties
    _power_device_type = None
    _battery_level_in_Ws = None
    _max_battery_level_in_Ws = None
    _charging_rate_in_W = None

    # Actor's mass in kg
    _mass = None

    _spacecraft_body_model = None
    _thermal_model = None
    _radiation_model = None
    _attitude_model = None

    # If radiation randomly restarted the device
    _was_interrupted = False

    # If radiation permanently killed this device
    _is_dead = False

    def __init__(
        self,
        name: str,
        epoch: pk.epoch,
    ) -> None:
        """Constructor for a spacecraft actor

        Args:
            name (str): Name of this actor
            epoch (pykep.epoch): Epoch at this pos
        """
        logger.trace("Instantiating SpacecraftActor.")
        super().__init__(name, epoch)

    def set_is_dead(self):
        """Sets this device to "is_dead=True" indicating permanent damage."""
        self._is_dead = True

    def set_was_interrupted(self):
        """Sets this device to "was_interrupted=True" indicating current activities were interrupted."""
        self._was_interrupted = True

    @property
    def was_interrupted(self) -> bool:
        """Returns whether the actor was interrupted in its activity.

        Returns:
            bool: True if device is interrupted.
        """
        return self._was_interrupted

    @property
    def is_dead(self) -> bool:
        """Returns whether the device experienced fatal radiation failure.

        Returns:
            bool: True if device is dead.
        """
        return self._is_dead

    @property
    def power_device_type(self):
        """Get the power device type

        Returns:
            PowerDeviceType: Type of power device.
        """
        return self._power_device_type

    @property
    def charging_rate_in_W(self):
        """Get the current charging rate.

        Returns:
            float: current charging rate in W.
        """
        return self._charging_rate_in_W

    @property
    def battery_level_in_Ws(self):
        """Get the current battery level.

        Returns:
            float: current battery level in wattseconds.
        """
        return self._battery_level_in_Ws

    @property
    def mass(self) -> float:
        """Returns actor's mass in kg.

        Returns:
            float: Mass
        """
        return self._mass

    @property
    def body_mesh(self) -> np.array:
        """Gives the mesh of the satellite.

        Returns:
            np.array: Mesh of the satellite.
        """
        return self._spacecraft_body_model._body_mesh

    @property
    def attitude_disturbances(self) -> list:
        """Gives attitude disturbances list.

        Returns:
            list: attitude disturbances list.
        """
        return self._attitude_model._disturbances

    @property
    def temperature_in_K(self) -> float:
        """Returns the current temperature of the actor in K.

        Returns:
            float: Actor temperature in Kelvin.
        """
        return self._thermal_model.temperature_in_K

    @property
    def temperature_in_C(self) -> float:
        """Returns the current temperature of the actor in C.

        Returns:
            float: Actor temperature in Celsius.
        """
        return self._thermal_model.temperature_in_K - 273.15

    @property
    def state_of_charge(self):
        """Get the current battery level as ratio of maximum.

        Returns:
            float: current battery level ratio in [0,1].
        """
        return self._battery_level_in_Ws / self._max_battery_level_in_Ws

    def discharge(self, consumption_rate_in_W: float, duration_in_s: float):
        """Discharge battery depending on power consumption.

        Args:
            consumption_rate_in_W (float): Consumption rate of the activity in Watt
            duration_in_s (float): How long the activity is performed in seconds
        """
        assert duration_in_s > 0, "Duration has to be positive"
        assert consumption_rate_in_W >= 0, "Power consumption rate has to be positive"

        power_consumption = consumption_rate_in_W * duration_in_s
        logger.debug(f"Discharging {power_consumption}")

        self = discharge_model.discharge(self, power_consumption)

        logger.debug(f"New battery level is {self._battery_level_in_Ws}Ws")

    def charge(self, duration_in_s: float):
        """Charges the actor from now for that period. Note that it is only
        verified the actor is neither at start nor end of the period in eclipse,
        thus short periods are preferable.

        Args:
            duration_in_s (float): How long the activity is performed in seconds
        """
        logger.debug(f"Charging actor {self} for {duration_in_s}s.")
        assert (
            duration_in_s > 0
        ), "Charging interval has to be positive but t1 was less or equal t0."

        self = charge_model.charge(self, duration_in_s)

        logger.debug(f"New battery level is {self.battery_level_in_Ws}")

    @property
    def attitude_in_rad(self):
        """Returns the current attitude of the actor in radians.

        Returns:
            list[floats]: actor attitude in radians.
        """
        if type(self._attitude_model._actor_attitude_in_rad) is np.ndarray:
            return np.ndarray.tolist(self._attitude_model._actor_attitude_in_rad)
        else:
            return self._attitude_model._actor_attitude_in_rad

    @property
    def attitude_in_deg(self):
        """Returns the current attitude of the actor in degrees.

        Returns:
            list[floats]: actor attitude in degrees.
        """
        if type(self._attitude_model._actor_attitude_in_rad) is np.ndarray:
            return np.ndarray.tolist(self._attitude_model._actor_attitude_in_rad * 180 / np.pi)
        else:
            return np.ndarray.tolist(
                np.array(self._attitude_model._actor_attitude_in_rad) * 180 / np.pi
            )

    @property
    def pointing_vector(self):
        """Returns the spacecraft pointing vector in the Earth-centered inertial frame.

        Returns:
            np.ndarray (x, y, z).
        """
        return self._attitude_model._actor_pointing_vector_eci

    @property
    def angular_velocity(self):
        """Returns the spacecraft angular velocity vector in the Earth-centered inertial frame.

        Returns:
            np.ndarray (owega_x, omega_y, omega_z).
        """
        return self._attitude_model._actor_angular_velocity_eci

    @property
    def body_moment_of_inertia_body(self) -> np.array:
        """Gives the moment of inertia of the actor, assuming constant density, with respect to the body frame.

        Returns:
            np.array: Mass moments of inertia for the actor

        I is the moment of inertia, in the form of [[Ixx Ixy Ixz]
                                                    [Iyx Iyy Iyx]
                                                    [Izx Izy Izz]]
        """
        return self._spacecraft_body_model._body_moment_of_inertia_body

    @property
    def body_center_of_gravity_body(self) -> np.array:
        """Gives the volumetric center of mass of the actor with respect to the body frame.

        Returns:
            np.array: Coordinates of the center of gravity of the mesh.
        """
        return self._spacecraft_body_model._body_center_of_gravity_body