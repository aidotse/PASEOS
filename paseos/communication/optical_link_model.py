import numpy as np
from loguru import logger
from .optical_receiver_model import OpticalReceiverModel
from .optical_transmitter_model import OpticalTransmitterModel
from .link_model import LinkModel
from .device_type import *
from ..actors.base_actor import BaseActor
import math


class OpticalLinkModel(LinkModel):
    """This class defines an optical link model, containing one transmitter and one receiver."""

    def __init__(
        self,
        transmitter_actor: BaseActor,
        transmitter_device_name: str,
        receiver_actor: BaseActor,
        receiver_device_name: str,
    ) -> None:
        """Initializes the model.

        Args:
            transmitter_actor (BaseActor): the transmitter in this link.
            transmitter_device_name (str): the name of the transmitter device.
            receiver_actor (BaseActor): the receiver in this link.
            receiver_device_name (str): the name of the receiver device.
        """
        self.wavelength = 1550e-9  # in m

        # Get the transmitter and receiver models from the actor
        transmitter = transmitter_actor.get_transmitter(transmitter_device_name)
        receiver = receiver_actor.get_receiver(receiver_device_name)

        super().__init__(
            transmitter_actor,
            transmitter,
            receiver_actor,
            receiver,
            frequency=299792458 / self.wavelength,
        )

        assert isinstance(transmitter, OpticalTransmitterModel), (
            "An optical transmitter is required " "for this optical link."
        )
        assert isinstance(
            receiver, OpticalReceiverModel
        ), "An optical receiver is required for this optical link."

        logger.debug("Initializing optical link model.")
        self.required_BER = 10e-3

        self.modulation_scheme = "OOK"
        self.required_s_n_margin = 3  # in dB

        self.receiver.set_gain(self.wavelength)
        self.transmitter.set_gain()

    def get_path_loss(self, slant_range: float) -> float:
        """Gets the path loss (free space loss) for a link.

        Args:
            slant_range (float): The slant range of the link, in meters

        Returns:
            The path loss (free space loss) in dB
        """
        assert slant_range > 0, "Slant range needs to be higher than 0 meters"

        return 20 * math.log10(4 * math.pi * slant_range / self.wavelength)

    def get_bitrate(self, slant_range: float, min_elevation_angle: float) -> float:
        """Gets the bitrate for a link based on current slant range and minimum elevation angle.

        Args:
            slant_range (float): The slant range of the link, in meters
            min_elevation_angle (float): The minimum elevation angle for this receiver, in degrees

        Returns:
            The bitrate in bps
        """
        assert slant_range > 0, "Slant range needs to be higher than 0 meters"
        assert min_elevation_angle >= 0, "Slant range needs to be higher than 0 meters"

        self.total_channel_loss = self.get_path_loss(slant_range)

        self.signal_at_receiver = self.transmitter.EIRP - self.total_channel_loss

        self.received_signal_power_with_gain = (
            self.signal_at_receiver
            + self.receiver.antenna_gain
            - self.receiver.line_losses
        )
        self.received_signal_power_with_margin = (
            self.received_signal_power_with_gain - self.required_s_n_margin
        )  # dBm
        self.received_signal_power_with_margin = (
            10 ** (self.received_signal_power_with_margin / 10) * 1e-3
        )  # nW
        bitrate = (
            self.received_signal_power_with_margin / 250 * 1550e-9 / 6.626e-34 / self.c
        )

        if bitrate < 0:
            bitrate = 0

        return bitrate
