"""Test to check the communication function(s)"""
import sys

sys.path.append("../..")

from paseos import SpacecraftActor

import pykep as pk


def from_epoch_to_s(epoch: pk.epoch):
    return (epoch.mjd2000 - pk.epoch(0).mjd2000) / pk.SEC2DAY


def test_communication_link():
    # create satellites where sat1 and sat2 starts from the same point but move along different orbit.
    # At t=1470s they will not be in line of sight anymore.
    earth = pk.planet.jpl_lp("earth")
    sat1 = SpacecraftActor(
        "sat1",
        position=[10000000, 1e-3, 1e-3],
        velocity=[1e-3, 8000, 1e-3],
        epoch=pk.epoch(0),
        central_body=earth,
        battery_level_in_Ws=1,
        max_battery_level_in_Ws=1,
        charging_rate_in_W=1,
    )
    sat2 = SpacecraftActor(
        "sat2",
        position=[10000000, 1e-3, 1e-3],
        velocity=[1e-3, -8000, 1e-3],
        epoch=pk.epoch(0),
        central_body=earth,
        battery_level_in_Ws=1,
        max_battery_level_in_Ws=1,
        charging_rate_in_W=1,
    )

    # Add communication link
    sat1.add_communication_links(name="link1", bandwidth_in_kbps=1)

    # Check communication link at == 0. Satellites shall be in line of sight
    (
        _,
        communication_window_end_time,
        transmitted_data_in_b,
    ) = sat1.get_communication_window(
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
    ) = sat1.get_communication_window(
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
    test_communication_link()
