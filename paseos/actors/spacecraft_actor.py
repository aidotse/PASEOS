from loguru import logger
import pykep as pk

from paseos.actors.base_actor import BaseActor


class SpacecraftActor(BaseActor):
    """This class models a spacecraft actor which in addition to pos,
    velocity also has additional constraints such as power/battery."""

    # Power-related properties
    _battery_level_in_Ws = None
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
        self._battery_level_in_Ws = battery_level_in_Ws
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

    def discharge(self, consumption_rate_in_W: float, duration_in_s: float):
        # TODO Check values for sensibility
        # TODO Reduce charge level according model
        raise NotImplementedError

    def charge(self, t0: pk.epoch, t1: pk.epoch):
        # TODO Check if in central bodies eclipse and how long
        # TODO Charge based on some model
        raise NotImplementedError
