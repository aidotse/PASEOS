import math
from loguru import logger

from .device_type import DeviceType
from .gain_calc import (calc_radio_gain_from_wavelength_diameter_db, calc_optical_gain_from_wavelength_diameter_db,
                        calc_gain_from_fwhm_db)


class TransmitterModel:
    """This class defines a simple transmitter model."""

    def __init__(
        self,
        input_power: float,
        power_efficiency: float,
        antenna_efficiency: float,
        line_losses: float,
        point_losses: float,
        device_type: DeviceType,
        antenna_gain: float = None,
        antenna_diameter: float = None,
        fwhm: float = None,
    ) -> None:
        """Initializes the model.

        Args:
            input_power (float): Input power into the signal amplifier, in W.
            power_efficiency (float): The power efficiency of the signal amplifier, determines
            the output power.
            antenna_efficiency (float): The efficiency of the antenna.
            line_losses (float): The line losses of the transmitter, in dB.
            point_losses (float): The pointing losses of the transmitter, in dB.
            antenna_gain (float): The gain of the antenna, either this or the diameter needs to
            be given so that gain
            can be determined.
            antenna_diameter (float): The diameter of the antenna, in m. Either this or the gain
            needs to be given.
        """

        logger.debug("Initializing general transmitter model.")

        assert (
            device_type is DeviceType.RADIO_TRANSMITTER or device_type is DeviceType.OPTICAL_TRANSMITTER
        ), "Device type must be RADIO_TRANSMITTER or OPTICAL_TRANSMITTER"

        self.device_type = device_type
        self.input_power = input_power
        self.antenna_efficiency = antenna_efficiency
        self.antenna_gain_db = antenna_gain
        self.antenna_diameter = antenna_diameter
        self.line_losses_db = line_losses
        self.pointing_losses_db = point_losses
        self.active = False
        self.power_efficiency = power_efficiency
        self.full_width_half_maximum = fwhm
        self.effective_isotropic_radiated_power_db = 0

        if device_type == DeviceType.RADIO_TRANSMITTER:
            self.output_power_db = 10 * math.log10(input_power * power_efficiency)  # dBW
        elif device_type == DeviceType.OPTICAL_TRANSMITTER:
            self.output_power_db = 10 * math.log10(input_power * power_efficiency * 1000)  # dBm

    def set_effective_isotropic_radiated_power_db(self) -> None:
        """Sets the Effective Isotropic Radiated Power (EIRP) for a transmitter."""
        self.effective_isotropic_radiated_power_db = (
            self.output_power_db - self.line_losses_db - self.pointing_losses_db + self.antenna_gain_db
        )

    def set_gain(self, wavelength: float) -> None:
        """Sets the gain of the transmitter.

        Args:
            wavelength (float): the wavelength of the transmitter, in m.
        """

        # If no constant gain value was passed and set in the constructor, it needs to be calculated
        if self.antenna_gain_db is None:
            if self.device_type == DeviceType.RADIO_TRANSMITTER:
                self.antenna_gain_db = calc_radio_gain_from_wavelength_diameter_db(
                    wavelength, self.antenna_diameter, self.antenna_efficiency
                )
            elif self.device_type == DeviceType.OPTICAL_TRANSMITTER:
                if self.antenna_diameter is not None:
                    self.antenna_gain_db = calc_optical_gain_from_wavelength_diameter_db(
                        wavelength, self.antenna_diameter, self.antenna_efficiency
                    )
                else:
                    self.antenna_gain_db = calc_gain_from_fwhm_db(self.full_width_half_maximum)

        self.set_effective_isotropic_radiated_power_db()

    def set_active_state(self, is_active: bool) -> None:
        """Sets the active state of the transmitter.

        Args:
            is_active (bool): whether the transmitter is active.
        """
        self.active = is_active
