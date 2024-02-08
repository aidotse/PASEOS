from loguru import logger
from ..utils.gain_calc import calc_gain_from_fwhm
from .transmitter_model import TransmitterModel
import math


class OpticalTransmitterModel(TransmitterModel):
    """This class defines a simple transmitter model."""

    def __init__(
            self,
            input_power: int,
            power_efficiency: float,
            antenna_efficiency: float,
            line_losses: int,
            point_losses: int,
            antenna_gain: int = 0,
            antenna_diameter: int = 0,
            fwhm: int = 0
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
            fwhm (int): full width at half maximum, in radians.
        """

        logger.debug("Initializing optical  transmitter model.")
        super().__init__(input_power, power_efficiency, antenna_efficiency, line_losses, point_losses, antenna_gain,
                         antenna_diameter)
        assert antenna_gain > 0 or antenna_diameter > 0 or fwhm > 0, ("Antenna gain or antenna diameter or "
                                                                      "FWHM needs to be higher than 0.")
        # assert (
        #         antenna_diameter > 0 and antenna_gain > 0 and fwhm > 0), ("Only set one of antenna gain, "
        #                                                                   "antenna diameter, and FWHM not multiple.")
        assert sum(param != 0 for param in (antenna_diameter, antenna_gain,
                                            fwhm)) <= 1, ("Only set one of antenna gain, "
                                                          "antenna diameter, and FWHM not multiple.")

        self.input_power = input_power
        self.power_efficiency = power_efficiency
        self.output_power = 10 * math.log10(input_power * power_efficiency * 1000)  # dBm
        self.FWHM = fwhm

    def set_gain(self):
        """Sets gain for a transmitter, based on the given gain, or antenna diameter and wavelength.
        """
        if self.antenna_gain == 0:
            self.antenna_gain = calc_gain_from_fwhm(self.FWHM)
        self.set_EIRP()
