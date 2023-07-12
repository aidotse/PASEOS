"""Test to check the communication function(s)"""
import sys

sys.path.append("../..")

from skspatial.objects import Sphere

from paseos import (
    SpacecraftActor,
    GroundstationActor,
    ActorBuilder,
    find_next_window,
    get_communication_window,
)

import pykep as pk
import numpy as np

from test_utils import _PASEOS_TESTS_EARTH_RADIUS


def from_epoch_to_s(epoch: pk.epoch):
    return (epoch.mjd2000 - pk.epoch(0).mjd2000) / pk.SEC2DAY


def setup_sentinel_example(t0):
    """Sets up the example with sentinel2B and maspolamas ground station."""
    """Tests the find_next_window function"""
    earth = pk.planet.jpl_lp("earth")

    # Define Sentinel 2 orbit
    sentinel2B = ActorBuilder.get_actor_scaffold("Sentinel2B", SpacecraftActor, t0)
    sentinel2B_line1 = "1 42063U 17013A   22300.18652110  .00000099  00000+0  54271-4 0  9998"
    sentinel2B_line2 = "2 42063  98.5693  13.0364 0001083 104.3232 255.8080 14.30819357294601"
    s2b = pk.planet.tle(sentinel2B_line1, sentinel2B_line2)

    # Calculating S2B ephemerides.
    sentinel2B_eph = s2b.eph(t0)

    ActorBuilder.set_orbit(
        actor=sentinel2B,
        position=sentinel2B_eph[0],
        velocity=sentinel2B_eph[1],
        epoch=t0,
        central_body=earth,
    )

    sentinel2B.set_central_body_shape(Sphere([0, 0, 0], _PASEOS_TESTS_EARTH_RADIUS))

    # Define ground station
    maspalomas_groundstation = ActorBuilder.get_actor_scaffold(
        name="maspalomas_groundstation", actor_type=GroundstationActor, epoch=t0
    )

    ActorBuilder.set_ground_station_location(
        maspalomas_groundstation, 27.7629, -15.6338, 205.1, minimum_altitude_angle=5
    )

    # Add communication link
    ActorBuilder.add_comm_device(sentinel2B, device_name="link1", bandwidth_in_kbps=1)
    return sentinel2B, maspalomas_groundstation


def test_find_next_window():
    # Test window from other test is found
    t0 = pk.epoch_from_string("2022-Oct-27 22:57:00")
    sentinel2B, maspalomas_groundstation = setup_sentinel_example(t0)

    start, length, transmittable_data = find_next_window(
        sentinel2B,
        local_actor_communication_link_name="link1",
        target_actor=maspalomas_groundstation,
        search_window_in_s=360,
        t0=t0,
    )

    assert np.isclose(start.mjd2000, 8335.957060185183)
    assert np.isclose(length, 740.0000001071021, rtol=0.01, atol=3.0)
    assert np.isclose(transmittable_data, 740000, rtol=0.01, atol=3000)

    # Test correct return if no window found
    t0 = pk.epoch_from_string("2022-Oct-27 20:00:00")
    sentinel2B, maspalomas_groundstation = setup_sentinel_example(t0)

    start, length, transmittable_data = find_next_window(
        sentinel2B,
        local_actor_communication_link_name="link1",
        target_actor=maspalomas_groundstation,
        search_window_in_s=360,
        t0=t0,
    )

    assert start is None
    assert length == 0
    assert transmittable_data == 0


def test_communication_link_sat_to_ground():
    """This test checks if the communication window between Sentinel
    and one of it's ground stations matches
    """
    t0 = pk.epoch_from_string("2022-Oct-27 22:58:09")
    sentinel2B, maspalomas_groundstation = setup_sentinel_example(t0)

    # Check again after communication_window_end_time
    (
        communication_window_start_time,
        communication_window_end_time,
        _,
    ) = get_communication_window(
        sentinel2B,
        local_actor_communication_link_name="link1",
        target_actor=maspalomas_groundstation,
        dt=1,
        t0=t0,
        data_to_send_in_b=1000000,
    )
    window_in_s = (
        communication_window_end_time.mjd2000 - communication_window_start_time.mjd2000
    ) * pk.DAY2SEC
    expected_window_in_s = 739.0000000305008
    assert np.isclose(expected_window_in_s, window_in_s)


def test_communication_link_sat_to_sat():
    # create satellites where sat1 and sat2 starts from the same point but move along different orbit.
    # At t=1470s they will not be in line of sight anymore.
    earth = pk.planet.jpl_lp("earth")
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    sat2 = ActorBuilder.get_actor_scaffold("sat2", SpacecraftActor, pk.epoch(0))

    ActorBuilder.set_orbit(
        sat1,
        position=[10000000, 1e-3, 1e-3],
        velocity=[1e-3, 8000, 1e-3],
        epoch=pk.epoch(0),
        central_body=earth,
    )
    ActorBuilder.set_orbit(
        sat2,
        position=[10000000, 1e-3, 1e-3],
        velocity=[1e-3, -8000, 1e-3],
        epoch=pk.epoch(0),
        central_body=earth,
    )

    sat1.set_central_body_shape(Sphere([0, 0, 0], _PASEOS_TESTS_EARTH_RADIUS))
    sat2.set_central_body_shape(Sphere([0, 0, 0], _PASEOS_TESTS_EARTH_RADIUS))

    # Add communication link
    ActorBuilder.add_comm_device(sat1, device_name="link1", bandwidth_in_kbps=1)

    # Check communication link at == 0. Satellites shall be in line of sight
    (
        _,
        communication_window_end_time,
        transmitted_data_in_b,
    ) = get_communication_window(
        sat1,
        local_actor_communication_link_name="link1",
        target_actor=sat2,
        dt=10,
        t0=pk.epoch(0),
        data_to_send_in_b=10000,
    )

    assert (from_epoch_to_s(communication_window_end_time) >= 10) and (
        transmitted_data_in_b == 10000
    )

    # Check again after communication_window_end_time
    (
        communication_window_start_time,
        communication_window_end_time,
        transmitted_data_in_b,
    ) = get_communication_window(
        sat1,
        local_actor_communication_link_name="link1",
        target_actor=sat2,
        dt=10,
        t0=communication_window_end_time,
        data_to_send_in_b=10000,
    )

    assert (transmitted_data_in_b == 0) and (
        from_epoch_to_s(communication_window_end_time)
        == from_epoch_to_s(communication_window_start_time)
    )


if __name__ == "__main__":
    # test_communication_link_sat_to_sat()
    test_communication_link_sat_to_ground()
