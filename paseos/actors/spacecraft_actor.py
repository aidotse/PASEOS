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
    battery_level_in_Ws = None
    _max_battery_level_in_Ws = None
    _charging_rate_in_W = None

    def __init__(
        self,
        name: str,
        position,
        velocity,
        epoch: pk.epoch,
        central_body: pk.planet,
        battery_level_in_Ws: float,
        max_battery_level_in_Ws: float,
        charging_rate_in_W: float,
    ) -> None:
        """Constructor for a spacecraft actor

        Args:
            name (str): Name of this actor
            position (list of floats): [x,y,z]
            velocity (list of floats): [vx,vy,vz]
            epoch (pykep.epoch): Epoch at this pos / velocity
            central_body (pk.planet): pykep central body
            battery_level_in_Ws (float): Current battery level in Watt seconds / Joule
            max_battery_level_in_Ws (float): Maximum battery level in Watt seconds / Joule
            charging_rate_in_W (float): Charging rate of the battery in Watt
        """
        logger.trace("Instantiating SpacecraftActor.")
        SpacecraftActor._check_init_value_sensibility(
            battery_level_in_Ws,
            max_battery_level_in_Ws,
            charging_rate_in_W,
        )
        self.battery_level_in_Ws = battery_level_in_Ws
        self._max_battery_level_in_Ws = max_battery_level_in_Ws
        self._charging_rate_in_W = charging_rate_in_W
        super().__init__(name, position, velocity, epoch, central_body)

    def _check_init_value_sensibility(
        battery_level_in_Ws: float,
        max_battery_level_in_Ws: float,
        charging_rate_in_W: float,
    ):
        """A function to check user inputs for sensibility

        Args:
            battery_level_in_Ws (float): Current battery level in Watt seconds / Joule
            max_battery_level_in_Ws (float): Maximum battery level in Watt seconds / Joule
            charging_rate_in_W (float): Charging rate of the battery in Watt
        """
        logger.trace("Checking constructor values for sensibility.")
        assert battery_level_in_Ws > 0, "Battery level must be non-negative"
        assert max_battery_level_in_Ws > 0, "Battery level must be non-negative"
        assert charging_rate_in_W > 0, "Battery level must be non-negative"

    @property
    def battery_level(self):
        return self.battery_level_in_Ws / self._max_battery_level_in_Ws

    def discharge(self, consumption_rate_in_W: float, duration_in_s: float):
        """Discharge battery depending on power consumption.

        Args:
            consumption_rate_in_W (float): Consumption rate of the activity in Watt
            duration_in_s (float): How long the activity is performed in seconds
        """
        assert duration_in_s > 0, "Duration has to be positive"
        assert consumption_rate_in_W > 0, "Power consumption rate has to be positive"

        power_consumption = consumption_rate_in_W * duration_in_s
        logger.debug(f"Discharging {power_consumption}")

        self = discharge_model.discharge(self, power_consumption)

    def charge(self, t0: pk.epoch, t1: pk.epoch):
        """Charges the actor during that period. Note that it is only
        verified the actor is neither at start nor end of the period in eclipse,
        thus short periods are preferable.

        Args:
            t0 (pk.epoch): Start of the charging interval
            t1 (pk.epoch): End of the charging interval

        """
        time_interval = (t1.mjd2000 - t0.mjd2000) * pk.DAY2SEC
        logger.debug(f"Charging actor {self} for {time_interval}s.")
        assert time_interval > 0, "Charging interval has to be positive but t1 was less or equal t0."

        if is_in_eclipse(self, central_body=self._central_body, t=t0) or is_in_eclipse(
            self, central_body=self._central_body, t=t1
        ):
            logger.debug("Actor is in eclipse, not charging.")
        else:
            self = charge_model.charge(self, time_interval)
        logger.debug(f"New battery level is {self.battery_level_in_Ws}")
