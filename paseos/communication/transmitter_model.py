import numpy as np
from loguru import logger
from ..utils.link_budget_calc  import *

class TransmitterModel:
    """This class defines a simple transmitter model."""

    def __init__(
        self,
        input_power: int,
        power_efficiency: float,
        antenna_efficiency: float,
        line_losses: int,
        point_losses: int,
        antenna_gain: int = 0,
        antenna_diameter: int = 0
    ) -> None:
        """Initializes the model.

        Args:
            transmission_type (string): Transmission type, radio or optical. Currently radio and optical is implemented
            input_power (int): Input power into the signal amplifier, in W.
            power_efficiency (float): The power efficiency of the signal amplifier, determines the output power.
            antenna_efficiency (float): The efficiency of the antenna.
            line_losses (int): The line losses of the transmitter, in dB.
            point_losses (int): The pointing losses of the transmitter, in dB.
            antenna_gain (int): The gain of the antenna, either this or the diameter needs to be given so that gain can be determined.
            antenna_diameter (int): The diameter of the antenna, in m. Either this or the gain needs to be given.
            full_angle_divergence (int): the full angle divergence of the transmit beam. For optical systems.
            antenna_type (str): Antenna type, currently only parabolic is implemented.
        """
        assert input_power > 0, "Input power needs to be higher than 0."
        assert power_efficiency > 0 and power_efficiency <= 1, "Power efficiency should be between 0 and 1."
        assert antenna_efficiency > 0 and antenna_efficiency <= 1, "Antenna efficiency should be between 0 and 1."
        assert line_losses >= 0, "Line losses needs to be 0 or higher."
        assert point_losses >= 0, "Pointing losses needs to be 0 or higher."
    
        logger.debug("Initializing general transmitter model.")

        self.antenna_efficiency = antenna_efficiency
        self.antenna_gain = antenna_gain
        self.antenna_diameter = antenna_diameter
        self.line_losses = line_losses
        self.point_losses = point_losses

    def set_EIRP(self):
        """Sets the Effective Isotropic Radiated Power (EIRP) for a transmitter.
        """
        self.EIRP = self.output_power - self.line_losses - self.point_losses + self.antenna_gain
    
    def set_gain(self):
        pass