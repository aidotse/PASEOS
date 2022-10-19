"""Test to check the communication function(s)"""
import sys

sys.path.append("../..")

from paseos import SpacecraftActor

import pykep as pk


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
    remaining_data_in_b, t_w_in_s = sat1.check_communication_link(
        "link1", sat2, 10, 0, 10000
    )

    assert (t_w_in_s >= 10) and (remaining_data_in_b == 0)

    # Check again after t_w_in_s
    remaining_data_in_b, t_w_in_s = sat1.check_communication_link(
        "link1", sat2, 10, t_w_in_s, 10000
    )

    assert remaining_data_in_b == 10000


if __name__ == "__main__":
    test_communication_link()
