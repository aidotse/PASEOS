from abc import ABC
from typing import Callable, Any

from loguru import logger
import pykep as pk
import numpy as np
from dotmap import DotMap

from ..central_body.is_in_line_of_sight import is_in_line_of_sight
from ..central_body.central_body import CentralBody


class BaseActor(ABC):
    """This (abstract) class is the baseline implementation of an actor
    (e.g. spacecraft, ground station) in the simulation. The abstraction allows
    some actors to have e.g. limited power (spacecraft) and others not to.
    """

    # Actor name, has to be unique
    name = None

    # Timestep this actor's info is at (excl. pos/vel)
    _local_time = None

    # Orbital parameters of the actor, stored in a pykep planet object
    _orbital_parameters = None

    # Custom function for orbital propagation
    _custom_orbit_propagator = None

    # Position if not defined by orbital parameters
    _position = None

    # Central body this actor is orbiting
    _central_body = None

    # Communication links dictionary
    _communication_devices = DotMap(_dynamic=False)

    # Tracks user-defined custom properties
    _custom_properties = DotMap(_dynamic=False)

    # Tracks the update function of user-defined custom properties
    # Which is updated in advance_time in paseos.py
    _custom_properties_update_function = DotMap(_dynamic=False)

    # Tracks the current activity
    _current_activity = None

    # Attitude disturbances experienced by the actor
    _disturbances = None

    # The following variables are used to track last evaluated state vectors to avoid recomputation.
    _previous_position = None
    _time_of_previous_position = None
    _previous_velocity = None
    _previous_eclipse_status = None
    _time_of_previous_eclipse_status = None
    _previous_altitude = None

    def __init__(self, name: str, epoch: pk.epoch) -> None:
        """Constructor for a base actor

        Args:
            name (str): Name of this actor
            epoch (pykep.epoch): Current local time of the actor.
        """
        logger.trace("Instantiating Actor.")
        super().__init__()
        self.name = name
        self._local_time = epoch

        self._communication_devices = DotMap(_dynamic=False)

    def get_custom_property(self, property_name: str) -> Any:
        """Returns the value of the specified custom property.

        Args:
            property_name (str): The name of the custom property.

        Returns:
            Any: The value of the custom property.
        """
        if property_name not in self._custom_properties:
            raise ValueError(f"Custom property '{property_name}' does not exist for actor {self}.")

        return self._custom_properties[property_name]

    @property
    def custom_properties(self):
        """Returns a dictionary of custom properties for this actor."""
        return self._custom_properties.toDict()

    @property
    def central_body(self) -> CentralBody:
        """Returns the central body this actor is orbiting."""
        return self._central_body

    def set_custom_property(self, property_name: str, value: Any) -> None:
        """Sets the value of the specified custom property.

        Args:
            property_name (str): The name of the custom property.
            value (Any): The value to set for the custom property.
        """
        if property_name not in self._custom_properties:
            raise ValueError(f"Custom property '{property_name}' does not exist for actor {self}.")

        self._custom_properties[property_name] = value

        logger.debug(f"Set custom property '{property_name}' to {value} for actor {self}.")

    def get_custom_property_update_function(self, property_name: str) -> Callable:
        """Returns the update function for the specified custom property.

        Args:
            property_name (str): The name of the custom property.

        Returns:
            Callable: The update function for the custom property.
        """
        if property_name not in self._custom_properties_update_function:
            raise ValueError(f"Custom property '{property_name}' does not exist for actor {self}.")

        return self._custom_properties_update_function[property_name]

    @property
    def has_central_body(self) -> bool:
        """Returns true if actor has a central body, else false.

        Returns:
            bool: bool indicating presence.
        """
        return hasattr(self, "_central_body") and self._central_body is not None

    @property
    def has_power_model(self) -> bool:
        """Returns true if actor's battery is modeled, else false.

        Returns:
            bool: bool indicating presence.
        """
        return hasattr(self, "_battery_level_in_Ws") and self._battery_level_in_Ws is not None

    @property
    def has_radiation_model(self) -> bool:
        """Returns true if actor's temperature is modeled, else false.

        Returns:
            bool: bool indicating presence.
        """
        return hasattr(self, "_radiation_model") and self._radiation_model is not None

    @property
    def has_thermal_model(self) -> bool:
        """Returns true if actor's temperature is modeled, else false.

        Returns:
            bool: bool indicating presence.
        """
        return hasattr(self, "_thermal_model") and self._thermal_model is not None

    @property
    def has_attitude_model(self) -> bool:
        """Returns true if actor's attitude is modeled, else false.

        Returns:
            bool: bool indicating presence.
        """
        return hasattr(self, "_attitude_model") and self._attitude_model is not None

    @property
    def has_attitude_disturbances(self) -> bool:
        """Returns true if actor has attitude disturbances attributed, else false.

        Returns:
            bool: bool indicating presence.
        """
        return hasattr(self, "_disturbances") and self._disturbances is not None

    @property
    def mass(self) -> float:
        """Returns actor's mass in kg.

        Returns:
            float: Mass
        """
        return self._mass

    @property
    def current_activity(self) -> str:
        """Returns the name of the activity the actor is currently performing.

        Returns:
            str: Activity name. None if no activity being performed.
        """
        return self._current_activity

    @property
    def local_time(self) -> pk.epoch:
        """Returns local time of the actor as pykep epoch. Use e.g. epoch.mjd2000 to get time in days.

        Returns:
            pk.epoch: local time of the actor
        """
        return self._local_time

    @property
    def communication_devices(self) -> DotMap:
        """Returns the communications devices.

        Returns:
            DotMap: Dictionary (DotMap) of communication devices.
        """
        return self._communication_devices

    @staticmethod
    def _check_init_value_sensibility(
        position,
        velocity,
    ):
        """A function to check user inputs for sensibility

        Args:
            position (list of floats): [x,y,z]
            velocity (list of floats): [vx,vy,vz]
        """
        logger.trace("Checking constructor values for sensibility.")
        assert len(position) == 3, "Position has to have 3 elements (x,y,z)"
        assert len(velocity) == 3, "Velocity has to have 3 elements (vx,vy,vz)"

    def __str__(self):
        return self.name

    def set_time(self, t: pk.epoch):
        """Updates the local time of the actor.

        Args:
            t (pk.epoch): Local time to set to.
        """
        self._local_time = t

    def charge(self, duration_in_s: float):
        """Charges the actor from now for that period. Note that it is only
        verified the actor is neither at start nor end of the period in eclipse,
        thus short periods are preferable.

        Args:
            duration_in_s (float): How long the activity is performed in seconds
        """
        pass

    def discharge(self, consumption_rate_in_W: float, duration_in_s: float):
        """Discharge battery depending on power consumption. Not implemented by default.

        Args:
            consumption_rate_in_W (float): Consumption rate of the activity in Watt
            duration_in_s (float): How long the activity is performed in seconds
        """
        pass

    def get_altitude(
        self,
        t0: pk.epoch = None,
    ) -> float:
        """Returns altitude above [0,0,0]. Will only compute if not computed for this timestep.

        Args:
            t0 (pk.epoch): Epoch to get altitude at. Defaults to local time.

        Returns:
            float: Altitude in meters.
        """
        if t0 is None:
            t0 = self._local_time
        if t0.mjd2000 == self._time_of_previous_position and self._previous_altitude is not None:
            return self._previous_altitude
        else:
            self._previous_altitude = np.sqrt(np.sum(np.power(self.get_position(t0), 2)))
            return self._previous_altitude

    def get_position(self, epoch: pk.epoch):
        """Compute the position of this actor at a specific time. Requires orbital parameters or position set.

        Args:
            epoch (pk.epoch): Time as pykep epoch

        Returns:
            np.array: [x,y,z] in meters
        """
        logger.trace(
            "Computing " + self.name + " position at time " + str(epoch.mjd2000) + " (mjd2000)."
        )

        if (
            self._orbital_parameters is not None or self._custom_orbit_propagator is not None
        ) and self._position is not None:
            raise ValueError(
                "Ambiguous position definition. Either set an orbit OR position with ActorBuilder."
            )

        # If the actor has no orbit, return position
        if self._orbital_parameters is None and self._custom_orbit_propagator is None:
            if self._position is not None:
                self._previous_position = self._position
                self._time_of_previous_position = epoch.mjd2000
                return self._position
        elif self._custom_orbit_propagator is not None:
            return self._custom_orbit_propagator(epoch)[0]
        else:
            return self._orbital_parameters.eph(epoch)[0]

        raise NotImplementedError(
            "No suitable way added to determine actor position. Either set an orbit or position with ActorBuilder."
        )

    def get_position_velocity(self, epoch: pk.epoch):
        """Compute the position / velocity of this actor at a specific time. Requires orbital parameters set.

        Args:
            epoch (pk.epoch): Time as pykep epoch.

        Returns:
            np.array: [x,y,z] in meters
        """

        if self._orbital_parameters is None and self._custom_orbit_propagator is None:
            raise NotImplementedError(
                "No suitable way added to determine actor velocity. Set an orbit with ActorBuilder."
            )

        logger.trace(
            "Computing "
            + self.name
            + " position / velocity at time "
            + str(epoch.mjd2000)
            + " (mjd2000)."
        )

        # Use either custom propagator or pykep to compute position / velocity
        if self._custom_orbit_propagator is not None:
            pos, vel = self._custom_orbit_propagator(epoch)
        else:
            pos, vel = self._orbital_parameters.eph(epoch)

        # Store the position / velocity for later use
        self._previous_position = pos
        self._previous_velocity = vel
        self._time_of_previous_position = epoch.mjd2000
        return pos, vel

    def get_disturbances(self):
        """Get the user-specified spacecraft attitude disturbances.

        Returns:
            list[string]: name of disturbances
        """
        return self._disturbances

    def is_in_line_of_sight(
        self,
        other_actor: "BaseActor",
        epoch: pk.epoch,
        minimum_altitude_angle: float = None,
        plot=False,
    ):
        """Determines whether a position is in line of sight of this actor

        Args:
            other_actor (BaseActor): The actor to check line of sight with
            epoch (pk,.epoch): Epoch at which to check the line of sight
            minimum_altitude_angle(float): The altitude angle (in degree) at which the actor has
            to be in relation to the ground station position to be visible. It has to be between 0 and 90.
            Only relevant if one of the actors is a ground station.
            plot (bool): Whether to plot a diagram illustrating the positions.

        Returns:
            bool: true if in line-of-sight.
        """
        return is_in_line_of_sight(self, other_actor, epoch, minimum_altitude_angle, plot)

    def is_in_eclipse(self, t: pk.epoch = None):
        """Checks if the actors is in eclipse at the specified time.

        Args:
            t (pk.epoch, optional): Time to check, if None will use current local actor time.
        """
        if t is None:
            t = self._local_time
        if t.mjd2000 == self._time_of_previous_eclipse_status:
            return self._previous_eclipse_status
        else:
            self._previous_eclipse_status = self._central_body.blocks_sun(self, t)
            self._time_of_last_eclipse_status = t.mjd2000
        return self._previous_eclipse_status
