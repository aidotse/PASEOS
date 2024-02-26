import math

from loguru import logger

from .receiver_model import ReceiverModel
from .transmitter_model import TransmitterModel
from ..actors.base_actor import BaseActor
from ..resources.constants import (C, WAVELENGTH_OPTICAL, REQUIRED_S_N_MARGIN_OPTICAL_DB, PHOTONS_PER_BIT, PLANCK_CONSTANT,
                                   BOLTZMANN_DB, REQUIRED_S_N_MARGIN_RADIO_DB, REQUIRED_S_N_RATIO_RADIO_DB)
from .device_type import DeviceType


class LinkModel:
    """This class defines a link model, containing one transmitter and one receiver."""

    # Keep track of bitrate throughout the simulation
    _bitrate_history = []

    # Keep track of line of sight throughout the simulation
    _line_of_sight_history = []

    # Keep track of distance throughout the simulation
    _distance_history = []

    # Keep track of elevation angle throughout the simulation
    _elevation_angle_history = []

    # Keep track of current bitrate throughout the simulation
    _current_bitrate = 0

    # Keep track of current line of sight throughout the simulation
    _current_line_of_sight = False

    # Keep track of current distance throughout the simulation
    _current_distance = 0

    # Keep track of current elevation angle throughout the simulation
    _current_elevation_angle = 0

    def __init__(
        self,
        transmitter_actor: BaseActor,
        transmitter_model: TransmitterModel,
        receiver_actor: BaseActor,
        receiver_model: ReceiverModel,
        frequency: float = 0,
    ) -> None:
        """Initializes the model.

        Args:
            transmitter_actor (BaseActor): the transmitter actor in this link.
            transmitter_model (TransmitterModel): the transmitter device model in this link.
            receiver_actor (BaseActor): the receiver actor in this link.
            receiver_model (ReceiverModel): the receiver device model.
        """

        logger.debug("Initializing link model.")
        if transmitter_model.device_type == DeviceType.RADIO_TRANSMITTER:
            self.wavelength = C / frequency  # in m
        elif transmitter_model.device_type == DeviceType.OPTICAL_TRANSMITTER:
            self.wavelength = WAVELENGTH_OPTICAL

        self.transmitter_actor = transmitter_actor
        self.transmitter = transmitter_model
        self.receiver_actor = receiver_actor
        self.receiver = receiver_model
        self._bitrate_history = []
        self._line_of_sight_history = []
        self._distance_history = []
        self._elevation_angle_history = []

        self.transmitter.set_gain(self.wavelength)
        self.receiver.set_gain_db(self.wavelength)

    def get_path_loss_db(self, slant_range: float) -> float:
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
        assert 90 >= min_elevation_angle >= 0, "Elevation angle needs to be between 0 and 90 degrees"
        bitrate = 0

        self.total_channel_loss_db = self.get_path_loss_db(slant_range)

        if self.transmitter.device_type == DeviceType.OPTICAL_TRANSMITTER:
            # Based on Giggenbach, D., Knopp, M. T., & Fuchs, C. (2023).
            # Link budget calculation in optical LEO satellite downlinks with on/off‐keying and
            # large signal divergence: A simplified methodology. International Journal of Satellite
            # Communications and Networking.
            self.signal_at_receiver_db = self.transmitter.effective_isotropic_radiated_power_db - self.total_channel_loss_db

            self.received_signal_power_with_gain_db = (
                self.signal_at_receiver_db + self.receiver.antenna_gain_db - self.receiver.line_losses_db
            )

            self.received_signal_power_with_margin_db = (
                self.received_signal_power_with_gain_db - REQUIRED_S_N_MARGIN_OPTICAL_DB
            )  # dBm

            self.received_signal_power_with_margin_nw = 10 ** (self.received_signal_power_with_margin_db / 10) * 1e-3  # nW

            bitrate = self.received_signal_power_with_margin_nw / PHOTONS_PER_BIT * WAVELENGTH_OPTICAL / PLANCK_CONSTANT / C
        elif self.transmitter.device_type == DeviceType.RADIO_TRANSMITTER:
            # Based on Kirkpatrick, D. (1999). Space mission analysis and design (Vol. 8).
            # J. R. Wertz, W. J. Larson, & D. Klungle (Eds.). Torrance: Microcosm.

            self.signal_at_receiver_db = self.transmitter.effective_isotropic_radiated_power_db - self.total_channel_loss_db

            self.s_n_power_density_db = (
                self.signal_at_receiver_db
                + self.receiver.antenna_gain_db
                - self.receiver.polarization_losses_db
                - self.receiver.line_losses_db
                - self.receiver.noise_temperature_db
                - BOLTZMANN_DB
            )
            self.s_n_power_density_including_margin_db = self.s_n_power_density_db - REQUIRED_S_N_MARGIN_RADIO_DB

            bitrate = 10 ** (-0.1 * (REQUIRED_S_N_RATIO_RADIO_DB - self.s_n_power_density_including_margin_db))

        if bitrate < 0:
            bitrate = 0

        return bitrate

    def set_bitrate(self, bitrate: float) -> None:
        """Sets the bitrate of this link for a certain epoch.

        Args:
            bitrate (float): The bitrate of this link, in bps
        """
        self._current_bitrate = bitrate

    def set_line_of_sight(self, state: bool) -> None:
        """Sets the line of sight of this link for a certain epoch,
        if there is a line of sight, the transmitter and receiver are set to active.

        Args:
            state (bool): The current line of sight state
        """
        self._current_line_of_sight = state
        if state:
            self.transmitter.set_active_state(True)
            self.receiver.set_active_state(True)
        else:
            self.transmitter.set_active_state(False)
            self.receiver.set_active_state(False)

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
