import math
from loguru import logger

from .gain_calc import calc_optical_gain_from_wavelength_diameter_db, calc_radio_gain_from_wavelength_diameter_db
from .device_type import DeviceType


class ReceiverModel:
    """This class defines a receiver model."""

    def __init__(
        self,
        device_type: DeviceType,
        line_losses: float,
        antenna_diameter: float = 0,
        antenna_gain: float = 0,
        polarization_losses: float = 0,
        noise_temperature: float = 0,
    ) -> None:
        """Initializes the model.

        Args:
            line_losses (float): The line losses of the receiver, in dB.
            antenna_diameter (float): The diameter of the antenna, in m.
            Either this or the gain needs to be given.
            antenna_gain (float): The gain of the antenna, either this or the diameter
            needs to be given so that gain can be determined.

        """

        logger.debug("Initializing receiver model.")
        assert (
            device_type is DeviceType.RADIO_RECEIVER or device_type is DeviceType.OPTICAL_RECEIVER
        ), "Device type must be RADIO_RECEIVER or OPTICAL_RECEIVER"
        self.device_type = device_type
        self.line_losses_db = line_losses  # in dB
        self.antenna_diameter = antenna_diameter  # in m
        self.antenna_gain_db = antenna_gain  # in dB

        if device_type == DeviceType.RADIO_RECEIVER:
            self.polarization_losses_db = polarization_losses  # in dB
            self.noise_temperature_db = 10 * math.log10(noise_temperature)  # in dBK

        self.active = False

    def set_gain_db(self, wavelength: float = 0) -> None:
        """Sets the gain of the receiver.

        Args:
            wavelength (float): the wavelength of the receiver, in m.
        """

        # If no constant gain value was passed and set in the constructor, it needs to be calculated
        if self.antenna_gain_db is None:
            if self.device_type == DeviceType.OPTICAL_RECEIVER:
                self.antenna_gain_db = calc_optical_gain_from_wavelength_diameter_db(wavelength, self.antenna_diameter, 1)
            elif self.device_type == DeviceType.RADIO_RECEIVER:
                self.antenna_gain_db = calc_radio_gain_from_wavelength_diameter_db(wavelength, self.antenna_diameter, 1)

    def set_active_state(self, is_active: bool) -> None:
        """Sets the active state of the transmitter.

        Args:
            is_active (bool): whether the transmitter is active.
        """
        self.active = is_active
