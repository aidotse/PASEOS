"""Tests to check the communication models creation and calculation function(s)"""
import numpy as np
import pykep as pk
import pytest

from paseos.actors.ground_station_actor import GroundstationActor
from paseos.communication.device_type import DeviceType
from paseos.communication.receiver_model import ReceiverModel
from paseos.communication.transmitter_model import TransmitterModel
from paseos.communication.link_model import LinkModel
from paseos import ActorBuilder, SpacecraftActor
from paseos.communication.link_budget_calc import calc_dist_and_alt_angle


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

    with pytest.raises(AssertionError, match="Frequency needs to be higher than 0 Hz."):
        ActorBuilder.add_comm_link(
            sat_actor,
            radio_name,
            maspalomas_groundstation,
            receiver_name,
            "link_1",
            frequency=-8675e6,
        )

    link_name = "link_1"
    ActorBuilder.add_comm_link(
        sat_actor, radio_name, maspalomas_groundstation, receiver_name, link_name, frequency=8675e6
    )

    link = sat_actor.get_comm_link(link_name)

    assert isinstance(link, LinkModel)


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
        match="Antenna gain or antenna diameter or fwhm needs to be set.",
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
        match="Only set one of antenna gain, antenna diameter and fwhm not multiple.",
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

    with pytest.raises(AssertionError, match="Polarization losses needs to be 0 or higher."):
        ActorBuilder.add_comm_device(
            actor=maspalomas_groundstation,
            device_name=receiver_name,
            noise_temperature=135,
            line_losses=1,
            polarization_losses=-3,
            antenna_gain=62.6,
            device_type=DeviceType.RADIO_RECEIVER,
        )
    with pytest.raises(AssertionError, match="Noise temperature needs to be 0 or higher."):
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

    with pytest.raises(AssertionError, match="Power efficiency should be between 0 and 1."):
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

    with pytest.raises(AssertionError, match="Power efficiency should be between 0 and 1."):
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

    with pytest.raises(AssertionError, match="Antenna efficiency should be between 0 and 1."):
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

    with pytest.raises(AssertionError, match="Antenna efficiency should be between 0 and 1."):
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

    with pytest.raises(AssertionError, match="Pointing losses needs to be 0 or higher."):
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
        match="Antenna gain or antenna diameter or fwhm needs to be set.",
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
        match="Only set one of antenna gain, antenna diameter and fwhm not multiple.",
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
    assert isinstance(transmitter, TransmitterModel)


def test_optical_transmitter_creation():
    t0 = pk.epoch_from_string("2023-Jan-04 20:00:00")
    sat_actor: SpacecraftActor = ActorBuilder.get_actor_scaffold(
        name="Sat", actor_type=SpacecraftActor, epoch=t0
    )

    with pytest.raises(
        AssertionError,
        match="Antenna gain or antenna diameter or fwhm needs to be set.",
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
        match="Only set one of antenna gain, antenna diameter and fwhm not multiple.",
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
        match="Only set one of antenna gain, antenna diameter and fwhm not multiple.",
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
        match="Only set one of antenna gain, antenna diameter and fwhm not multiple.",
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
        match="Only set one of antenna gain, antenna diameter and fwhm not multiple.",
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
    assert isinstance(transmitter, TransmitterModel)


def test_bitrate_calculation():
    # Radio input based on Kirkpatrick, D. (1999). Space mission analysis and design (Vol. 8).
    # J. R. Wertz, W. J. Larson, & D. Klungle (Eds.). Torrance: Microcosm.

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
        polarization_losses=0.3,
        antenna_gain=39.1,
        device_type=DeviceType.RADIO_RECEIVER,
    )

    sat_actor: SpacecraftActor = ActorBuilder.get_actor_scaffold(
        name="Sat", actor_type=SpacecraftActor, epoch=t0
    )
    radio_name = "sat_radio_transmitter_1"

    ActorBuilder.add_comm_device(
        actor=sat_actor,
        device_name=radio_name,
        input_power=40,
        power_efficiency=0.5,
        antenna_efficiency=1,
        line_losses=1,
        point_losses=8.5,
        antenna_gain=14.2,
        device_type=DeviceType.RADIO_TRANSMITTER,
    )

    optical_transmitter_name = "sat_optical_transmitter_1"

    # Optical transmitter input based on Giggenbach, D., Knopp, M. T., & Fuchs, C. (2023).
    # Link budget calculation in optical LEO satellite downlinks with on/off‐keying and
    # large signal divergence: A simplified methodology. International Journal of Satellite
    # Communications and Networking.
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

    # Optical receiver input based on
    # https://www.eoportal.org/satellite-missions/edrs#lct-laser-communication-terminal
    ActorBuilder.add_comm_device(
        actor=comms_sat,
        device_name=optical_receiver_name,
        line_losses=4.1,
        antenna_diameter=135e-3,
        device_type=DeviceType.OPTICAL_RECEIVER,
    )

    ActorBuilder.add_comm_link(
        sat_actor, radio_name, maspalomas_groundstation, receiver_name, "link_1", frequency=2.2e9
    )

    # Based on hand calculations
    link_model = sat_actor.get_comm_link("link_1")
    radio_bitrate = link_model.get_bitrate(2831e3, 0)
    assert np.isclose(radio_bitrate, 114e6, 0.01, 1000)

    ActorBuilder.add_comm_link(
        sat_actor, optical_transmitter_name, comms_sat, optical_receiver_name, "optical_link_1"
    )

    # Based on hand calculations
    optical_link_model = sat_actor.get_comm_link("optical_link_1")
    optical_bitrate = optical_link_model.get_bitrate(595e3, 0)
    assert np.isclose(optical_bitrate, 86.5e6, 0.01, 1000)


def test_communication_link_sat_to_sat():
    earth = pk.planet.jpl_lp("earth")
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    sat2 = ActorBuilder.get_actor_scaffold("sat2", SpacecraftActor, pk.epoch(0))

    altitude = 500e3
    inclination = 0
    W_1 = 0
    W_2 = 30 * pk.DEG2RAD
    argPeriapsis = 0

    a = altitude + 6371000  # in [m], earth radius included
    e = 0
    i = inclination * pk.DEG2RAD
    w = argPeriapsis * pk.DEG2RAD
    E = 0

    r_1, v_1 = pk.core.par2ic([a, e, i, W_1, w, E], 1)
    r_2, v_2 = pk.core.par2ic([a, e, i, W_2, w, E], 1)

    ActorBuilder.set_orbit(
        sat1,
        position=r_1,
        velocity=v_1,
        epoch=pk.epoch(0),
        central_body=earth,
    )
    ActorBuilder.set_orbit(
        sat2,
        position=r_2,
        velocity=v_2,
        epoch=pk.epoch(0),
        central_body=earth,
    )

    dist, elevation_angle = calc_dist_and_alt_angle(sat1, sat2, sat1.local_time)

    # Based on hand calculations
    assert np.isclose(dist, 3556691, 0.01, 100)


if __name__ == "__main__":
    test_bitrate_calculation()
    test_communication_link_sat_to_sat()
    test_link_creation()
    test_optical_receiver_creation()
    test_optical_transmitter_creation()
    test_radio_receiver_creation()
    test_radio_transmitter_creation()
    test_receiver_creation()
    test_transmitter_creation()
