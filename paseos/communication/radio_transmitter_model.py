import math
from loguru import logger
from ..utils.gain_calc import calc_radio_gain_from_wavelength_diameter
from .transmitter_model import TransmitterModel

class RadioTransmitterModel(TransmitterModel):
    """This class defines a radio transmitter model."""

    def __init__(
        self,
        input_power: int,
        power_efficiency: float,
        antenna_efficiency: float,
        line_losses: float,
        point_losses: float,
        antenna_gain: float = 0,
        antenna_diameter: float = 0
    ) -> None:
        """Initializes the model.

        Args:
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
        super().__init__(input_power, power_efficiency, antenna_efficiency, line_losses, point_losses, antenna_gain, antenna_diameter)
        assert antenna_gain > 0 or antenna_diameter > 0, "Antenna gain or antenna diameter needs to be higher than 0."
        assert not (antenna_diameter != 0 and antenna_gain != 0),  "Only set one of antenna gain and antenna diameter, not both."

        self.input_power = input_power
        self.power_efficiency = power_efficiency
        self.output_power = 10 * math.log10(input_power * power_efficiency) # dBW

        logger.debug("Initializing radio transmitter model.")
        

    def set_gain(self, wavelength):
        """Sets gain for a transmitter, based on the given gain, or antenna diameter and wavelength.

        Args:
            wavelength (int): The wavelength of the link, in meters
        """
        if self.antenna_gain == 0:
            self.antenna_gain = calc_radio_gain_from_wavelength_diameter(wavelength, self.antenna_diameter, self.antenna_efficiency)
  
        self.set_EIRP()
