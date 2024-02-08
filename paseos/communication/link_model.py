import numpy as np
from loguru import logger
from .receiver_model import ReceiverModel
from .transmitter_model import TransmitterModel
from .device_type import *
from ..actors.base_actor import BaseActor
import math


class LinkModel:
    """This class defines a link model, containing one transmitter and one receiver."""

    _bitrate_history = []
    _line_of_sight_history = []
    _distance_history = []
    _elevation_angle_history = []

    _current_bitrate = 0
    _current_line_of_sight = False
    _current_distance = 0
    _current_elevation_angle = 0

    def __init__(
            self,
            transmitter_actor: BaseActor,
            transmitter_model: TransmitterModel,
            receiver_actor: BaseActor,
            receiver_model: ReceiverModel,
            frequency: float
    ) -> None:
        """Initializes the model.

        Args:
            transmitter_actor (BaseActor): the transmitter actor in this link.
            transmitter_model (TransmitterModel): the transmitter device model in this link.
            receiver_actor (BaseActor): the receiver actor in this link.
            receiver_model (ReceiverModel): the receiver device model.
        """
        # assert isinstance(transmitter, TransmitterModel), "A transmitter is required for this link."
        assert isinstance(receiver_model, ReceiverModel), "A receiver is required for this link."

        logger.debug("Initializing link model.")
        self.c = 299792458
        self.wavelength = self.c / frequency  # in m
        self.transmitter_actor = transmitter_actor
        self.transmitter = transmitter_model
        self.receiver_actor = receiver_actor
        self.receiver = receiver_model
        self._bitrate_history = []
        self._line_of_sight_history = []
        self._distance_history = []
        self._elevation_angle_history = []

    def get_path_loss(self, slant_range: float) -> float:
        """Gets the path loss (free space loss) for a link.

        Args:
            slant_range (float): The slant range of the link, in meters

        Returns:
            The path loss (free space loss) in dB
        """
        assert slant_range > 0, "Slant range needs to be higher than 0 meters"

        return 20 * math.log10(4 * math.pi * slant_range / self.wavelength)

    def set_bitrate(self, bitrate: float) -> None:
        """Sets the bitrate of this link for a certain epoch.

        Args:
            bitrate (float): The bitrate of this link, in bps
        """
        self._current_bitrate = bitrate

    def set_line_of_sight(self, state: bool) -> None:
        """Sets the line of sight of this link for a certain epoch,
        if there is a line of sight, the transmitter is set to active.

        Args:
            state (bool): The current line of sight state
        """
        self._current_line_of_sight = state
        if state:
            self.transmitter.set_active(True)
        else:
            self.transmitter.set_active(False)

    def set_distance(self, distance: float) -> None:
        """Sets the distance of this link for a certain epoch.

        Args:
            distance (float): The slant range of the link, in meters
        """
        self._current_distance = distance

    def set_elevation_angle(self, angle: float) -> None:
        """Sets the elevation angle of this link for a certain epoch.

        Args:
            angle (float): The elevation angle, in degrees
        """
        self._current_elevation_angle = angle

    def save_state(self) -> None:
        """Saves the state of this link."""
        self._bitrate_history.append(self._current_bitrate)
        self._line_of_sight_history.append(self._current_line_of_sight)
        self._distance_history.append(self._current_distance)
        self._elevation_angle_history.append(self._current_elevation_angle)

    @property
    def bitrate_history(self):
        return self._bitrate_history

    @property
    def line_of_sight_history(self):
        return self._line_of_sight_history

    @property
    def distance_history(self):
        return self._distance_history

    @property
    def elevation_angle_history(self):
        return self._elevation_angle_history
