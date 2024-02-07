import numpy as np
from loguru import logger
import math
from ..utils.link_budget_calc import *
from .receiver_model import ReceiverModel

class RadioReceiverModel(ReceiverModel):
    """This class defines a radio receiver model."""

    def __init__(
        self,
        line_losses: int,
        polarization_loss: int ,
        noise_temperature: int,
        antenna_diameter: int = 0, 
        antenna_gain: int = 0
    ) -> None:
        """Initializes the model.

        Args:
            line_losses (int): The line losses of the receiver, in dB.
            polarization_loss (int): The polarization losses of the receiver, in dB.
            noise_temperature (int): The noise temperature of the receiver, in K.
            antenna_diameter (int): The diameter of the antenna, in m. Either this or the gain needs to be given.
            antenna_gain (int): The gain of the antenna, either this or the diameter needs to be given so that gain can be determined.
            
        """

        super().__init__(line_losses, antenna_diameter, antenna_gain)
        assert polarization_loss >= 0, "Polarization losses needs to be 0 or higher."
        assert noise_temperature > 0, "Noise temperature needs to be higher than 0."
        logger.debug("Initializing radio receiver model.")
        
        self.polarization_loss = polarization_loss # in dB
        self.noise_temperature = 10 * math.log10(noise_temperature) # in dBK

    def set_gain(self, wavelength):
        """Sets gain for a receiver, based on the given gain, or antenna diameter and wavelength.

        Args:
            wavelength (int): The wavelength of the link, in meters
        """
        if self.antenna_gain == 0:
            self.antenna_gain = calc_radio_gain_from_wavelength_diameter(wavelength, self.antenna_diameter, 1)