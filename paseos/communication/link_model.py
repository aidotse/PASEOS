import numpy as np
from loguru import logger
from .receiver_model import ReceiverModel
from .transmitter_model import TransmitterModel
from .link_type import *
from ..actors.base_actor import BaseActor
import math

class LinkModel:
    """This class defines a link model, containing one transmitter and one receiver."""

    _bitrate_history = []
    _current_bitrate = 0
    def __init__(
        self,
        transmitter_actor: BaseActor,
        transmitter: TransmitterModel,
        receiver_actor: BaseActor,
        receiver: ReceiverModel,
        frequency: int
    ) -> None:
        """Initializes the model.

        Args:
            transmitter (TransmitterModel): The transmitter in this link.
            receiver (ReceiverModel): The receiver in this link.      
        """
        assert isinstance(transmitter, TransmitterModel), "A transmitter is required for this link."
        assert isinstance(receiver, ReceiverModel), "A receiver is required for this link."

        logger.debug("Initializing link model.")
        self.c = 299792458
        self.wavelength = self.c / frequency # in m
        self.transmitter_actor = transmitter_actor
        self.transmitter = transmitter
        self.receiver_actor = receiver_actor
        self.receiver = receiver
    
    def get_path_loss(self, slant_range):
        """Gets the path loss (free space loss) for a link.

        Args:
            slant_range (int): The slant range of the link, in meters

        Returns:
            The path loss (free space loss) in dB
        """
        assert slant_range > 0, "Slant range needs to be higher than 0 meters"

        return 20 * math.log10(4 * math.pi * slant_range  / self.wavelength)

    def set_bitrate(self, bitrate):
        self._current_bitrate = bitrate

    def save_bitrate(self):
        self._bitrate_history.append(self._current_bitrate)
    
    @property
    def bitrate_history(self):
        return self._bitrate_history