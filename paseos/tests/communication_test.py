"""Test to check the link_budget_calc function(s)"""
import pytest

from paseos.communication.transmitter_model import TransmitterModel
from paseos.communication.radio_transmitter_model import RadioTransmitterModel
from paseos.communication.optical_transmitter_model import OpticalTransmitterModel
from paseos.communication.receiver_model import ReceiverModel
from paseos.communication.radio_receiver_model import RadioReceiverModel
from paseos.communication.optical_receiver_model import OpticalReceiverModel
from paseos.communication.link_model import LinkModel
from paseos.communication.radio_link_model import RadioLinkModel
from paseos.communication.optical_link_model import OpticalLinkModel
import pykep as pk
import numpy as np
import pdb
import re

def test_link_creation():
    radio_receiver = RadioReceiverModel(5, 5, 200, antenna_diameter=15)
    radio_transmitter = RadioTransmitterModel(1, 0.5, 0.5, 5, 5, antenna_diameter=0.3)
    
    optical_receiver = OpticalReceiverModel(5, 0.3)
    optical_transmitter = OpticalTransmitterModel(2, 0.5, 1, 1, 3, FWHM=1E-3)

    with pytest.raises(AssertionError, match="An optical transmitter is required for this optical link."):
        link = OpticalLinkModel(radio_transmitter, optical_receiver)
    with pytest.raises(AssertionError, match="An optical receiver is required for this optical link."):
        link = OpticalLinkModel(optical_transmitter, radio_receiver)

    with pytest.raises(AssertionError, match="A radio transmitter is required for this radio link."):
        link = RadioLinkModel(optical_transmitter, radio_receiver, 8675E6)
    with pytest.raises(AssertionError, match="A radio receiver is required for this radio link."):
        link = RadioLinkModel(radio_transmitter, optical_receiver, 8675E6)

    with pytest.raises(AssertionError, match="Frequency needs to be higher than 0 Hz."):
        link = RadioLinkModel(radio_transmitter, radio_receiver, -8675E6)


    optical_link = OpticalLinkModel(optical_transmitter, optical_receiver)
    assert isinstance(optical_link, OpticalLinkModel)

    radio_link = RadioLinkModel(radio_transmitter, radio_receiver, 8675E6)
    assert isinstance(radio_link, RadioLinkModel)

def test_receiver_creation():
    with pytest.raises(AssertionError, match="Line losses needs to be 0 or higher."):
            receiver = ReceiverModel(-5, antenna_diameter=15)
    with pytest.raises(AssertionError, match="Antenna gain or antenna diameter needs to be higher than 0."):
            receiver = ReceiverModel(5)
    with pytest.raises(AssertionError, match="Only set one of antenna gain and antenna diameter, not both."):
            receiver = ReceiverModel(5, antenna_diameter=15, antenna_gain=60)

    receiver = ReceiverModel(5, antenna_diameter=15)
    assert isinstance(receiver, ReceiverModel)

def test_radio_receiver_creation():
    with pytest.raises(AssertionError, match="Polarization losses needs to be 0 or higher."):
        receiver = RadioReceiverModel(5, -5, 200, antenna_diameter=15)
    with pytest.raises(AssertionError, match="Noise temperature needs to be higher than 0."):
        receiver = RadioReceiverModel(5, 5, -200, antenna_diameter=15)
    
    receiver = RadioReceiverModel(5, 5, 200, antenna_diameter=15)
    assert isinstance(receiver, RadioReceiverModel)
    assert isinstance(receiver, ReceiverModel)

def test_optical_receiver_creation():
    
    receiver = OpticalReceiverModel(5, antenna_diameter=15)
    assert isinstance(receiver, OpticalReceiverModel)
    assert isinstance(receiver, ReceiverModel)

def test_transmitter_creation():
    with pytest.raises(AssertionError, match="Input power needs to be higher than 0."):
        transmitter = TransmitterModel(-1, 0.5, 0.5, 5, 5, antenna_diameter=0.3)

    with pytest.raises(AssertionError, match="Power efficiency should be between 0 and 1."):
        transmitter = TransmitterModel(10, 1.5, 0.5, 5, 5, antenna_diameter=0.3)

    with pytest.raises(AssertionError, match="Power efficiency should be between 0 and 1."):
        transmitter = TransmitterModel(10, -0.5, 0.5, 5, 5, antenna_diameter=0.3)

    with pytest.raises(AssertionError, match="Antenna efficiency should be between 0 and 1."):
        transmitter = TransmitterModel(10, 0.5, 1.5, 5, 5, antenna_diameter=0.3)

    with pytest.raises(AssertionError, match="Antenna efficiency should be between 0 and 1."):
        transmitter = TransmitterModel(10, 0.5,-0.5, 5, 5, antenna_diameter=0.3)

    with pytest.raises(AssertionError, match="Line losses needs to be 0 or higher."):
            transmitter = TransmitterModel(10, 0.5, 0.5, -5, 5, antenna_diameter=0.3)

    with pytest.raises(AssertionError, match="Pointing losses needs to be 0 or higher."):
        transmitter = TransmitterModel(10, 0.5, 0.5, 5, -5, antenna_diameter=0.3)
    
    transmitter = TransmitterModel(1, 0.5, 0.5, 5, 5, antenna_diameter=0.3)
    assert isinstance(transmitter, TransmitterModel)

def test_radio_transmitter_creation():
    with pytest.raises(AssertionError, match="Antenna gain or antenna diameter needs to be higher than 0."):
        transmitter = RadioTransmitterModel(10, 0.5, 0.5, 5, 5)

    with pytest.raises(AssertionError, match="Only set one of antenna gain and antenna diameter, not both."):
        transmitter = RadioTransmitterModel(10, 0.5, 0.5, 5, 5, antenna_gain = 10, antenna_diameter=10)

    with pytest.raises(AssertionError, match="Antenna gain or antenna diameter needs to be higher than 0."):
        transmitter = RadioTransmitterModel(10, 0.5, 0.5, 5, 5)
    
    transmitter = RadioTransmitterModel(1, 0.5, 0.5, 5, 5, antenna_diameter=0.3)
    assert isinstance(transmitter, RadioTransmitterModel)
    assert isinstance(transmitter, TransmitterModel)

def test_optical_transmitter_creation():
    with pytest.raises(AssertionError, match="Antenna gain or antenna diameter needs to be higher than 0."):
        transmitter = RadioTransmitterModel(10, 0.5, 0.5, 5, 5)

    with pytest.raises(AssertionError, match="Only set one of antenna gain and antenna diameter, not both."):
        transmitter = RadioTransmitterModel(10, 0.5, 0.5, 5, 5, antenna_gain = 10, antenna_diameter=10)

    with pytest.raises(AssertionError, match="Antenna gain or antenna diameter needs to be higher than 0."):
        transmitter = RadioTransmitterModel(10, 0.5, 0.5, 5, 5)
    
    transmitter = RadioTransmitterModel(1, 0.5, 0.5, 5, 5, antenna_diameter=0.3)
    assert isinstance(transmitter, RadioTransmitterModel)
    assert isinstance(transmitter, TransmitterModel)


def test_bitrate_calculation():
    radio_transmitter = RadioTransmitterModel(2, 0.5, 0.5, 1, 5, antenna_diameter=0.3)
    radio_receiver = RadioReceiverModel(1, 3, 135, antenna_gain=62.6)
    radio_link = RadioLinkModel(radio_transmitter, radio_receiver, 8475E6)

    radio_bitrate = radio_link.get_bitrate(1932E3, 10)
    assert np.isclose(radio_bitrate, 2083559918, 0.01, 1000)

    optical_transmitter = OpticalTransmitterModel(1, 1, 1, 1, 3, FWHM = 1E-3)
    optical_receiver = OpticalReceiverModel(4.1, antenna_gain=114.2)
    optical_link = OpticalLinkModel(optical_transmitter, optical_receiver)

    optical_bitrate = optical_link.get_bitrate(595E3, 0)
    assert np.isclose(optical_bitrate, 303720940, 0.01, 1000)

if __name__ == "__main__":
    test_transmitter_creation()
    test_radio_transmitter_creation
    test_receiver_creation()
    test_link_creation()
    test_bitrate_calculation()
