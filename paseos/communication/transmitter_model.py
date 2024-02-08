from loguru import logger


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
            input_power (int): Input power into the signal amplifier, in W.
            power_efficiency (float): The power efficiency of the signal amplifier, determines the output power.
            antenna_efficiency (float): The efficiency of the antenna.
            line_losses (int): The line losses of the transmitter, in dB.
            point_losses (int): The pointing losses of the transmitter, in dB.
            antenna_gain (int): The gain of the antenna, either this or the diameter needs to be given so that gain
            can be determined.
            antenna_diameter (int): The diameter of the antenna, in m. Either this or the gain needs to be given.
        """
        assert input_power > 0, "Input power needs to be higher than 0."
        assert 0 < power_efficiency <= 1, "Power efficiency should be between 0 and 1."
        assert 0 < antenna_efficiency <= 1, "Antenna efficiency should be between 0 and 1."
        assert line_losses >= 0, "Line losses needs to be 0 or higher."
        assert point_losses >= 0, "Pointing losses needs to be 0 or higher."
    
        logger.debug("Initializing general transmitter model.")
        self.input_power = input_power
        self.antenna_efficiency = antenna_efficiency
        self.antenna_gain = antenna_gain
        self.antenna_diameter = antenna_diameter
        self.line_losses = line_losses
        self.point_losses = point_losses
        self.active = False

    def set_EIRP(self):
        """Sets the Effective Isotropic Radiated Power (EIRP) for a transmitter."""
        self.EIRP = self.output_power - self.line_losses - self.point_losses + self.antenna_gain
    
    def set_gain(self):
        pass

    def set_active(self, state: bool):
        """Sets the active state of the transmitter.

            Args:
                state (bool): whether the transmitter is active.
        """
        self.active = state
