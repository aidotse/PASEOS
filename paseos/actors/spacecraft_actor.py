from loguru import logger
import pykep as pk

from paseos.actors.base_actor import BaseActor
from paseos.power import discharge_model
from paseos.power import charge_model
from paseos.power.is_in_eclipse import is_in_eclipse


class SpacecraftActor(BaseActor):
    """This class models a spacecraft actor which in addition to pos,
    velocity also has additional constraints such as power/battery."""

    # Power-related properties
    _battery_level_in_Ws = None
    _max_battery_level_in_Ws = None
    _charging_rate_in_W = None

    # Actor's mass in kg
    _mass = None

    _thermal_model = None

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
    def temperature_in_K(self) -> float:
        """Returns the current temperature of the actor in K.

        Returns:
            float: Temperature in Kelvin.
        """
        return self._thermal_model.temperature_in_K

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

        # Compute end of charging time
        t1 = pk.epoch(self.local_time.mjd2000 + duration_in_s * pk.SEC2DAY)
        if is_in_eclipse(
            self, central_body=self._central_body, t=self.local_time
        ) or is_in_eclipse(self, central_body=self._central_body, t=t1):
            logger.debug("Actor is in eclipse, not charging.")
        else:
            self = charge_model.charge(self, duration_in_s)
        logger.debug(f"New battery level is {self.battery_level_in_Ws}")
