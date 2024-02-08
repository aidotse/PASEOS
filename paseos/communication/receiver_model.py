from loguru import logger


class ReceiverModel:
    """This class defines a receiver model."""

    def __init__(
        self, line_losses: float, antenna_diameter: float = 0, antenna_gain: float = 0
    ) -> None:
        """Initializes the model.

        Args:
            line_losses (float): The line losses of the receiver, in dB.
            antenna_diameter (float): The diameter of the antenna, in m.
            Either this or the gain needs to be given.
            antenna_gain (float): The gain of the antenna, either this or the diameter
            needs to be given so that gain can be determined.

        """
        assert line_losses >= 0, "Line losses needs to be 0 or higher."
        assert (
            antenna_gain > 0 or antenna_diameter > 0
        ), "Antenna gain or antenna diameter needs to be higher than 0."
        assert not (antenna_diameter != 0 and antenna_gain != 0), (
            "Only set one of antenna gain and " "antenna diameter, not both."
        )
        logger.debug("Initializing receiver model.")

        self.line_losses = line_losses  # in dB
        self.antenna_diameter = antenna_diameter  # in m
        self.antenna_gain = antenna_gain  # in dB

    def set_gain(self, wavelength: float = 0) -> None:
        pass
