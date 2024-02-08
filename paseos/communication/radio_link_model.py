import numpy as np
from loguru import logger
from .radio_receiver_model import RadioReceiverModel
from .radio_transmitter_model import RadioTransmitterModel
from .link_model import LinkModel
from ..actors.spacecraft_actor import SpacecraftActor
from ..actors.ground_station_actor import GroundstationActor
from ..actors.base_actor import BaseActor

import math


class RadioLinkModel(LinkModel):
    """This class defines a link model, containing one transmitter and one receiver."""

    def __init__(
            self,
            transmitter_actor: BaseActor,
            transmitter_device_name: str,
            receiver_actor: BaseActor,
            receiver_device_name: str,
            frequency: float,
    ) -> None:
        """Initializes the model.

        Args:
            transmitter_actor (BaseActor): the transmitter in this link.
            transmitter_device_name (str): the name of the transmitter device.
            receiver_actor (BaseActor): the receiver in this link.
            receiver_device_name (str): the name of the receiver device.  
            frequency (float): The frequency of this link, in Hz.
        """

        # Get the actual transmitter and receiver models
        transmitter = transmitter_actor.get_transmitter(transmitter_device_name)
        receiver = receiver_actor.get_receiver(receiver_device_name)

        super().__init__(transmitter_actor, transmitter, receiver_actor, receiver, frequency)

        assert frequency > 0, "Frequency needs to be higher than 0 Hz."
        assert isinstance(transmitter, RadioTransmitterModel), "A radio transmitter is required for this radio link."
        assert isinstance(receiver, RadioReceiverModel), "A radio receiver is required for this radio link."

        logger.debug("Initializing radio link model.")
        self.transmitter = transmitter
        self.receiver = receiver
        self.required_BER = 10E-5
        self.frequency = frequency  # in Hz
        self.modulation_scheme = "BPSK"
        self.zenith_atmospheric_attenuation = 0.5  # in dB
        self.required_s_n_ratio = 9.6  # in dB
        self.required_s_n_margin = 3  # in dB

        self.receiver.set_gain(self.wavelength)
        self.transmitter.set_gain(self.wavelength)

    def get_path_loss(self, slant_range) -> float:
        """Gets the path loss (free space loss) for a link.

        Args:
            slant_range (int): The slant range of the link, in meters

        Returns:
            The path loss (free space loss) in dB
        """
        assert slant_range > 0, "Slant range needs to be higher than 0 meters"

        return 20 * math.log10(4 * math.pi * slant_range / self.wavelength)

    def get_max_atmospheric_loss(self, min_elevation_angle) -> float:
        """Gets the maximal atmospheric loss for a link.

        Args:
            min_elevation_angle (float): The minimum elevation angle for this receiver, in degrees

        Returns:
            The path loss (free space loss) in dB
        """
        assert min_elevation_angle > 0, "Slant range needs to be higher than 0 meters"

        return self.zenith_atmospheric_attenuation / math.sin(min_elevation_angle * math.pi / 180)

    def get_bitrate(self, slant_range, min_elevation_angle) -> float:
        """Gets the bitrate for a link based on current slant range and minimum elevation angle.

        Args:
            slant_range (int): The slant range of the link, in meters
            min_elevation_angle (float): The minimum elevation angle for this receiver, in degrees

        Returns:
            The bitrate in bps
        """
        assert slant_range > 0, "Slant range needs to be higher than 0 meters"
        assert min_elevation_angle >= 0, "Slant range needs to be higher than 0 meters"

        boltzmann_constant = 228.6
        self.total_channel_loss = self.get_path_loss(slant_range) + self.get_max_atmospheric_loss(min_elevation_angle)

        self.signal_at_receiver = self.transmitter.EIRP - self.total_channel_loss

        self.s_n_power_density = self.signal_at_receiver + self.receiver.antenna_gain - self.receiver.polarization_loss - self.receiver.line_losses - self.receiver.noise_temperature + boltzmann_constant
        self.s_n_power_density_including_margin = self.s_n_power_density - self.required_s_n_margin
        bitrate = 10 ** (-0.1 * (self.required_s_n_ratio - self.s_n_power_density_including_margin))

        if bitrate < 0:
            bitrate = 0

        return bitrate
