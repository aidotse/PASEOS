from loguru import logger
from .receiver_model import ReceiverModel

class OpticalReceiverModel(ReceiverModel):
    """This class defines an optical receiver model."""

    def __init__(
        self,
        line_losses: int,
        antenna_diameter: int = 0, 
        antenna_gain: int = 0
    ) -> None:
        """Initializes the model.

        Args:
            line_losses (int): The line losses of the receiver, in dB.
            antenna_diameter (int): The diameter of the antenna, in m. Either this or the gain needs to be given.
            antenna_gain (int): The gain of the antenna, either this or the diameter needs to be given so that gain can be determined.
            
        """

        super().__init__(line_losses, antenna_diameter, antenna_gain)
        logger.debug("Initializing optical receiver model.")

    def set_gain(self, wavelength):
        """Sets gain for a receiver, based on the given gain, or antenna diameter and wavelength.

        Args:
            wavelength (int): The wavelength of the link, in meters
        """
        if self.antenna_gain == 0:
            self.antenna_gain = calc_optical_gain_from_wavelength_diameter(wavelength, self.antenna_diameter, 1)