"""Tests to check the communication models creation and calculation function(s)"""
import numpy as np
import pykep as pk
import pytest

from paseos.actors.actor_builder import ActorBuilder
from paseos.actors.ground_station_actor import GroundstationActor
from paseos.actors.spacecraft_actor import SpacecraftActor
from paseos.communication.device_type import DeviceType
from paseos.communication.optical_link_model import OpticalLinkModel
from paseos.communication.optical_receiver_model import OpticalReceiverModel
from paseos.communication.optical_transmitter_model import OpticalTransmitterModel
from paseos.communication.radio_link_model import RadioLinkModel
from paseos.communication.radio_receiver_model import RadioReceiverModel
from paseos.communication.radio_transmitter_model import RadioTransmitterModel
from paseos.communication.receiver_model import ReceiverModel
from paseos.communication.transmitter_model import TransmitterModel


def test_link_creation():
    t0 = pk.epoch_from_string("2023-Jan-04 20:00:00")
    maspalomas_groundstation = ActorBuilder.get_actor_scaffold(
        name="maspalomas_groundstation", actor_type=GroundstationActor, epoch=t0
    )
    receiver_name = "maspalomas_radio_receiver_1"

    ActorBuilder.add_comm_device(
        actor=maspalomas_groundstation,
        device_name=receiver_name,
        noise_temperature=135,
        line_losses=1,
        polarization_losses=3,
        antenna_gain=62.6,
        device_type=DeviceType.RADIO_RECEIVER,
    )

    sat_actor: SpacecraftActor = ActorBuilder.get_actor_scaffold(
        name="Sat", actor_type=SpacecraftActor, epoch=t0
    )
    radio_name = "sat_radio_transmitter_1"
    optical_transmitter_name = "sat_optical_transmitter_1"

    ActorBuilder.add_comm_device(
        actor=sat_actor,
        device_name=optical_transmitter_name,
        input_power=1,
        power_efficiency=1,
        antenna_efficiency=1,
        line_losses=1,
        point_losses=3,
        fwhm=1e-3,
        device_type=DeviceType.OPTICAL_TRANSMITTER,
    )

    ActorBuilder.add_comm_device(
        actor=sat_actor,
        device_name=radio_name,
        input_power=2,
        power_efficiency=0.5,
        antenna_efficiency=0.5,
        line_losses=1,
        point_losses=5,
        antenna_diameter=0.3,
        device_type=DeviceType.RADIO_TRANSMITTER,
    )

    comms_sat: SpacecraftActor = ActorBuilder.get_actor_scaffold(
        name="Comms", actor_type=SpacecraftActor, epoch=t0
    )
    optical_receiver_name = "optical_receiver_1"
    ActorBuilder.add_comm_device(
        actor=comms_sat,
        device_name=optical_receiver_name,
        line_losses=4.1,
        antenna_gain=114.2,
        device_type=DeviceType.OPTICAL_RECEIVER,
    )

    with pytest.raises(
            AssertionError,
            match="An optical transmitter is required for this optical link.",
    ):
        OpticalLinkModel(sat_actor, radio_name, comms_sat, optical_receiver_name)
    with pytest.raises(
            AssertionError, match="An optical receiver is required for this optical link."
    ):
        OpticalLinkModel(
            sat_actor, optical_transmitter_name, maspalomas_groundstation, receiver_name
        )

    with pytest.raises(
            AssertionError, match="A radio transmitter is required for this radio link."
    ):
        RadioLinkModel(
            sat_actor,
            optical_transmitter_name,
            maspalomas_groundstation,
            receiver_name,
            8675e6,
        )
    with pytest.raises(
            AssertionError, match="A radio receiver is required for this radio link."
    ):
        RadioLinkModel(
            sat_actor, radio_name, comms_sat, optical_receiver_name, 8675e6
        )

    with pytest.raises(AssertionError, match="Frequency needs to be higher than 0 Hz."):
        RadioLinkModel(
            sat_actor, radio_name, maspalomas_groundstation, receiver_name, -8675e6
        )

    optical_link = OpticalLinkModel(
        sat_actor, optical_transmitter_name, comms_sat, optical_receiver_name
    )
    assert isinstance(optical_link, OpticalLinkModel)

    radio_link = RadioLinkModel(
        sat_actor, radio_name, maspalomas_groundstation, receiver_name, 8675e6
    )
    assert isinstance(radio_link, RadioLinkModel)


def test_receiver_creation():
    t0 = pk.epoch_from_string("2023-Jan-04 20:00:00")
    maspalomas_groundstation = ActorBuilder.get_actor_scaffold(
        name="maspalomas_groundstation", actor_type=GroundstationActor, epoch=t0
    )
    ActorBuilder.set_ground_station_location(
        maspalomas_groundstation,
        latitude=27.7629,
        longitude=-15.6338,
        elevation=205.1,
        minimum_altitude_angle=5,
    )

    receiver_name = "maspalomas_radio_receiver_1"

    with pytest.raises(AssertionError, match="Line losses needs to be 0 or higher."):
        ActorBuilder.add_comm_device(
            actor=maspalomas_groundstation,
            device_name=receiver_name,
            noise_temperature=135,
            line_losses=-1,
            polarization_losses=3,
            antenna_gain=62.6,
            device_type=DeviceType.RADIO_RECEIVER,
        )
    with pytest.raises(
            AssertionError,
            match="Antenna gain or antenna diameter needs to be higher than 0.",
    ):
        ActorBuilder.add_comm_device(
            actor=maspalomas_groundstation,
            device_name=receiver_name,
            noise_temperature=135,
            line_losses=1,
            polarization_losses=3,
            device_type=DeviceType.RADIO_RECEIVER,
        )
    with pytest.raises(
            AssertionError,
            match="Only set one of antenna gain and antenna diameter, not both.",
    ):
        ActorBuilder.add_comm_device(
            actor=maspalomas_groundstation,
            device_name=receiver_name,
            noise_temperature=135,
            line_losses=1,
            polarization_losses=3,
            antenna_gain=62.6,
            antenna_diameter=2,
            device_type=DeviceType.RADIO_RECEIVER,
        )

    ActorBuilder.add_comm_device(
        actor=maspalomas_groundstation,
        device_name=receiver_name,
        noise_temperature=135,
        line_losses=1,
        polarization_losses=3,
        antenna_gain=62.6,
        device_type=DeviceType.RADIO_RECEIVER,
    )

    receiver = maspalomas_groundstation.get_receiver(receiver_name)
    assert isinstance(receiver, ReceiverModel)


def test_radio_receiver_creation():
    t0 = pk.epoch_from_string("2023-Jan-04 20:00:00")
    maspalomas_groundstation = ActorBuilder.get_actor_scaffold(
        name="maspalomas_groundstation", actor_type=GroundstationActor, epoch=t0
    )
    ActorBuilder.set_ground_station_location(
        maspalomas_groundstation,
        latitude=27.7629,
        longitude=-15.6338,
        elevation=205.1,
        minimum_altitude_angle=5,
    )

    receiver_name = "maspalomas_radio_receiver_1"

    with pytest.raises(
            AssertionError, match="Polarization losses needs to be 0 or higher."
    ):
        ActorBuilder.add_comm_device(
            actor=maspalomas_groundstation,
            device_name=receiver_name,
            noise_temperature=135,
            line_losses=1,
            polarization_losses=-3,
            antenna_gain=62.6,
            device_type=DeviceType.RADIO_RECEIVER,
        )
    with pytest.raises(
            AssertionError, match="Noise temperature needs to be higher than 0."
    ):
        ActorBuilder.add_comm_device(
            actor=maspalomas_groundstation,
            device_name=receiver_name,
            noise_temperature=-135,
            line_losses=1,
            polarization_losses=3,
            antenna_gain=62.6,
            device_type=DeviceType.RADIO_RECEIVER,
        )

    ActorBuilder.add_comm_device(
        actor=maspalomas_groundstation,
        device_name=receiver_name,
        noise_temperature=135,
        line_losses=1,
        polarization_losses=3,
        antenna_gain=62.6,
        device_type=DeviceType.RADIO_RECEIVER,
    )

    receiver = maspalomas_groundstation.get_receiver(receiver_name)
    assert isinstance(receiver, RadioReceiverModel)
    assert isinstance(receiver, ReceiverModel)


def test_optical_receiver_creation():
    t0 = pk.epoch_from_string("2023-Jan-04 20:00:00")
    comms_sat: SpacecraftActor = ActorBuilder.get_actor_scaffold(
        name="Sat", actor_type=SpacecraftActor, epoch=t0
    )
    optical_receiver_name = "optical_receiver_1"
    ActorBuilder.add_comm_device(
        actor=comms_sat,
        device_name=optical_receiver_name,
        line_losses=4.1,
        antenna_gain=114.2,
        device_type=DeviceType.OPTICAL_RECEIVER,
    )

    receiver = comms_sat.get_receiver(optical_receiver_name)
    assert isinstance(receiver, OpticalReceiverModel)
    assert isinstance(receiver, ReceiverModel)


def test_transmitter_creation():
    t0 = pk.epoch_from_string("2023-Jan-04 20:00:00")
    sat_actor: SpacecraftActor = ActorBuilder.get_actor_scaffold(
        name="Sat", actor_type=SpacecraftActor, epoch=t0
    )
    radio_name = "sat_radio_transmitter_1"

    with pytest.raises(AssertionError, match="Input power needs to be higher than 0."):
        ActorBuilder.add_comm_device(
            actor=sat_actor,
            device_name=radio_name,
            input_power=-2,
            power_efficiency=0.5,
            antenna_efficiency=0.5,
            line_losses=1,
            point_losses=5,
            antenna_diameter=0.3,
            device_type=DeviceType.RADIO_TRANSMITTER,
        )

    with pytest.raises(
            AssertionError, match="Power efficiency should be between 0 and 1."
    ):
        ActorBuilder.add_comm_device(
            actor=sat_actor,
            device_name=radio_name,
            input_power=2,
            power_efficiency=1.5,
            antenna_efficiency=0.5,
            line_losses=1,
            point_losses=5,
            antenna_diameter=0.3,
            device_type=DeviceType.RADIO_TRANSMITTER,
        )

    with pytest.raises(
            AssertionError, match="Power efficiency should be between 0 and 1."
    ):
        ActorBuilder.add_comm_device(
            actor=sat_actor,
            device_name=radio_name,
            input_power=2,
            power_efficiency=-0.5,
            antenna_efficiency=0.5,
            line_losses=1,
            point_losses=5,
            antenna_diameter=0.3,
            device_type=DeviceType.RADIO_TRANSMITTER,
        )

    with pytest.raises(
            AssertionError, match="Antenna efficiency should be between 0 and 1."
    ):
        ActorBuilder.add_comm_device(
            actor=sat_actor,
            device_name=radio_name,
            input_power=2,
            power_efficiency=0.5,
            antenna_efficiency=1.5,
            line_losses=1,
            point_losses=5,
            antenna_diameter=0.3,
            device_type=DeviceType.RADIO_TRANSMITTER,
        )

    with pytest.raises(
            AssertionError, match="Antenna efficiency should be between 0 and 1."
    ):
        ActorBuilder.add_comm_device(
            actor=sat_actor,
            device_name=radio_name,
            input_power=2,
            power_efficiency=0.5,
            antenna_efficiency=-0.5,
            line_losses=1,
            point_losses=5,
            antenna_diameter=0.3,
            device_type=DeviceType.RADIO_TRANSMITTER,
        )

    with pytest.raises(AssertionError, match="Line losses needs to be 0 or higher."):
        ActorBuilder.add_comm_device(
            actor=sat_actor,
            device_name=radio_name,
            input_power=2,
            power_efficiency=0.5,
            antenna_efficiency=0.5,
            line_losses=-1,
            point_losses=5,
            antenna_diameter=0.3,
            device_type=DeviceType.RADIO_TRANSMITTER,
        )

    with pytest.raises(
            AssertionError, match="Pointing losses needs to be 0 or higher."
    ):
        ActorBuilder.add_comm_device(
            actor=sat_actor,
            device_name=radio_name,
            input_power=2,
            power_efficiency=0.5,
            antenna_efficiency=0.5,
            line_losses=1,
            point_losses=-5,
            antenna_diameter=0.3,
            device_type=DeviceType.RADIO_TRANSMITTER,
        )


def test_radio_transmitter_creation():
    t0 = pk.epoch_from_string("2023-Jan-04 20:00:00")
    sat_actor: SpacecraftActor = ActorBuilder.get_actor_scaffold(
        name="Sat", actor_type=SpacecraftActor, epoch=t0
    )
    radio_name = "sat_radio_transmitter_1"

    with pytest.raises(
            AssertionError,
            match="Antenna gain or antenna diameter needs to be higher than 0.",
    ):
        ActorBuilder.add_comm_device(
            actor=sat_actor,
            device_name=radio_name,
            input_power=2,
            power_efficiency=0.5,
            antenna_efficiency=0.5,
            line_losses=1,
            point_losses=5,
            device_type=DeviceType.RADIO_TRANSMITTER,
        )

    with pytest.raises(
            AssertionError,
            match="Only set one of antenna gain and antenna diameter, not both.",
    ):
        ActorBuilder.add_comm_device(
            actor=sat_actor,
            device_name=radio_name,
            input_power=2,
            power_efficiency=0.5,
            antenna_efficiency=0.5,
            antenna_diameter=1,
            antenna_gain=100,
            line_losses=1,
            point_losses=5,
            device_type=DeviceType.RADIO_TRANSMITTER,
        )

    ActorBuilder.add_comm_device(
        actor=sat_actor,
        device_name=radio_name,
        input_power=2,
        power_efficiency=0.5,
        antenna_efficiency=0.5,
        line_losses=1,
        point_losses=5,
        antenna_diameter=0.3,
        device_type=DeviceType.RADIO_TRANSMITTER,
    )
    transmitter = sat_actor.get_transmitter(radio_name)
    assert isinstance(transmitter, RadioTransmitterModel)
    assert isinstance(transmitter, TransmitterModel)


def test_optical_transmitter_creation():
    t0 = pk.epoch_from_string("2023-Jan-04 20:00:00")
    sat_actor: SpacecraftActor = ActorBuilder.get_actor_scaffold(
        name="Sat", actor_type=SpacecraftActor, epoch=t0
    )

    with pytest.raises(
            AssertionError,
            match="Antenna gain or antenna diameter or FWHM needs to be higher than 0.",
    ):
        ActorBuilder.add_comm_device(
            actor=sat_actor,
            device_name="optical_transmitter_name",
            input_power=1,
            power_efficiency=1,
            antenna_efficiency=1,
            line_losses=1,
            point_losses=3,
            device_type=DeviceType.OPTICAL_TRANSMITTER,
        )

    with pytest.raises(
            AssertionError,
            match="Only set one of antenna gain, antenna diameter, and FWHM not multiple.",
    ):
        ActorBuilder.add_comm_device(
            actor=sat_actor,
            device_name="optical_transmitter_name",
            input_power=1,
            power_efficiency=1,
            antenna_efficiency=1,
            line_losses=1,
            point_losses=3,
            antenna_gain=100,
            fwhm=1e-3,
            device_type=DeviceType.OPTICAL_TRANSMITTER,
        )
    with pytest.raises(
            AssertionError,
            match="Only set one of antenna gain, antenna diameter, and FWHM not multiple.",
    ):
        ActorBuilder.add_comm_device(
            actor=sat_actor,
            device_name="optical_transmitter_name",
            input_power=1,
            power_efficiency=1,
            antenna_efficiency=1,
            line_losses=1,
            point_losses=3,
            antenna_gain=100,
            antenna_diameter=1,
            device_type=DeviceType.OPTICAL_TRANSMITTER,
        )
    with pytest.raises(
            AssertionError,
            match="Only set one of antenna gain, antenna diameter, and FWHM not multiple.",
    ):
        ActorBuilder.add_comm_device(
            actor=sat_actor,
            device_name="optical_transmitter_name",
            input_power=1,
            power_efficiency=1,
            antenna_efficiency=1,
            line_losses=1,
            point_losses=3,
            fwhm=1e-3,
            antenna_diameter=1,
            device_type=DeviceType.OPTICAL_TRANSMITTER,
        )
    with pytest.raises(
            AssertionError,
            match="Only set one of antenna gain, antenna diameter, and FWHM not multiple.",
    ):
        ActorBuilder.add_comm_device(
            actor=sat_actor,
            device_name="optical_transmitter_name",
            input_power=1,
            power_efficiency=1,
            antenna_efficiency=1,
            line_losses=1,
            point_losses=3,
            fwhm=1e-3,
            antenna_diameter=1,
            antenna_gain=100,
            device_type=DeviceType.OPTICAL_TRANSMITTER,
        )

    ActorBuilder.add_comm_device(
        actor=sat_actor,
        device_name="optical_transmitter_name",
        input_power=1,
        power_efficiency=1,
        antenna_efficiency=1,
        line_losses=1,
        point_losses=3,
        fwhm=1e-3,
        device_type=DeviceType.OPTICAL_TRANSMITTER,
    )
    transmitter = sat_actor.get_transmitter("optical_transmitter_name")
    assert isinstance(transmitter, OpticalTransmitterModel)
    assert isinstance(transmitter, TransmitterModel)


def test_bitrate_calculation():
    t0 = pk.epoch_from_string("2023-Jan-04 20:00:00")
    maspalomas_groundstation = ActorBuilder.get_actor_scaffold(
        name="maspalomas_groundstation", actor_type=GroundstationActor, epoch=t0
    )
    receiver_name = "maspalomas_radio_receiver_1"

    ActorBuilder.add_comm_device(
        actor=maspalomas_groundstation,
        device_name=receiver_name,
        noise_temperature=135,
        line_losses=1,
        polarization_losses=3,
        antenna_gain=62.6,
        device_type=DeviceType.RADIO_RECEIVER,
    )

    sat_actor: SpacecraftActor = ActorBuilder.get_actor_scaffold(
        name="Sat", actor_type=SpacecraftActor, epoch=t0
    )
    radio_name = "sat_radio_transmitter_1"

    ActorBuilder.add_comm_device(
        actor=sat_actor,
        device_name=radio_name,
        input_power=2,
        power_efficiency=0.5,
        antenna_efficiency=0.5,
        line_losses=1,
        point_losses=5,
        antenna_diameter=0.3,
        device_type=DeviceType.RADIO_TRANSMITTER,
    )

    optical_transmitter_name = "sat_optical_transmitter_1"

    ActorBuilder.add_comm_device(
        actor=sat_actor,
        device_name=optical_transmitter_name,
        input_power=1,
        power_efficiency=1,
        antenna_efficiency=1,
        line_losses=1,
        point_losses=3,
        fwhm=1e-3,
        device_type=DeviceType.OPTICAL_TRANSMITTER,
    )

    comms_sat: SpacecraftActor = ActorBuilder.get_actor_scaffold(
        name="Comms", actor_type=SpacecraftActor, epoch=t0
    )
    optical_receiver_name = "optical_receiver_1"
    ActorBuilder.add_comm_device(
        actor=comms_sat,
        device_name=optical_receiver_name,
        line_losses=4.1,
        antenna_gain=114.2,
        device_type=DeviceType.OPTICAL_RECEIVER,
    )

    radio_link = RadioLinkModel(
        sat_actor, radio_name, maspalomas_groundstation, receiver_name, 8675e6
    )

    radio_bitrate = radio_link.get_bitrate(1932e3, 10)
    assert np.isclose(radio_bitrate, 2083559918, 0.01, 1000)

    optical_link = OpticalLinkModel(
        sat_actor, optical_transmitter_name, comms_sat, optical_receiver_name
    )

    optical_bitrate = optical_link.get_bitrate(595e3, 0)
    assert np.isclose(optical_bitrate, 303720940, 0.01, 1000)


if __name__ == "__main__":
    test_transmitter_creation()
    test_radio_transmitter_creation()
    test_receiver_creation()
    test_link_creation()
    test_bitrate_calculation()
