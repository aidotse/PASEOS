import numpy as np
from loguru import logger
from .optical_receiver_model import OpticalReceiverModel
from .optical_transmitter_model import OpticalTransmitterModel
from .link_model import LinkModel
from .link_type import *
from ..actors.base_actor import BaseActor
import math

class OpticalLinkModel(LinkModel):
    """This class defines an ptical link model, containing one transmitter and one receiver."""

    def __init__(
        self,
        transmitterActor: BaseActor,
        transmitterName,
        receiverActor: BaseActor,
        receiverName,
    ) -> None:
        """Initializes the model.

        Args:
            transmitter (TransmitterModel): The transmitter in this link.
            receiver (ReceiverModel): The receiver in this link.
            frequency (int): The frequency of this link, in Hz.
            required_BER (int): The required bit error rate (BER), 10^-5 by default.
            modulation_scheme (string): The modulation scheme for this link, currently only BPSK implemented
            coding_scheme (string): The coding scheme for this link, currently not implemented         
        """
        self.wavelength = 1550E-9 # in m
        transmitter = transmitterActor.get_transmitter(transmitterName)
        receiver = receiverActor.get_receiver(receiverName)

        super().__init__(transmitterActor, transmitter, receiverActor, receiver, 299792458/self.wavelength)
        
        assert isinstance(transmitter, OpticalTransmitterModel), "An optical transmitter is required for this optical link."
        assert isinstance(receiver, OpticalReceiverModel), "An optical receiver is required for this optical link."

        logger.debug("Initializing optical link model.")
        self.required_BER = 10E-3
        
        self.modulation_scheme = "OOK"
        self.required_s_n_margin = 3 # in dB

        self.receiver.set_gain(self.wavelength)
        self.transmitter.set_gain()
    
    def get_path_loss(self, slant_range):
        """Gets the path loss (free space loss) for a link.

        Args:
            slant_range (int): The slant range of the link, in meters

        Returns:
            The path loss (free space loss) in dB
        """
        assert slant_range > 0, "Slant range needs to be higher than 0 meters"

        return 20 * math.log10(4 * math.pi * slant_range  / self.wavelength)
    
    def get_bitrate(self, slant_range, min_elevation_angle):
        """Gets the bitrate for a link based on current slant range and minimum elevation angle.

        Args:
            slant_range (int): The slant range of the link, in meters
            min_elevation_angle (float): The minimum elevation angle for this receiver, in degrees

        Returns:
            The bitrate in bps
        """
        assert slant_range > 0, "Slant range needs to be higher than 0 meters"
        assert min_elevation_angle >= 0, "Slant range needs to be higher than 0 meters"

        self.total_channel_loss = self.get_path_loss(slant_range)

        self.signal_at_receiver = self.transmitter.EIRP - self.total_channel_loss

        self.received_signal_power_with_gain = self.signal_at_receiver + self.receiver.antenna_gain - self.receiver.line_losses
        self.received_signal_power_with_margin = self.received_signal_power_with_gain - self.required_s_n_margin #dBm
        self.received_signal_power_with_margin = 10**(self.received_signal_power_with_margin / 10) * 1E-3 #nW
        bitrate = self.received_signal_power_with_margin / 250 * 1550E-9 / 6.626E-34 / self.c

        if bitrate < 0:
            bitrate = 0
    
        return bitrate