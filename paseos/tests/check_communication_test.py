"""Test to check the communication function(s)"""
import sys

sys.path.append("../..")

import paseos
from paseos import SpacecraftActor

import pykep as pk


def test_communication_link():
    # create satellites where sat1 and 2 are in sight of each other (as well as sat 1 and 3)
    # but sat 2 and 3 are on opposite sides of the planet
    earth = pk.planet.jpl_lp("earth")
    sat1 = SpacecraftActor("sat1", position=[10000000, 0,0], velocity=[0, 8000, 0], epoch=pk.epoch(0), central_body=earth, battery_level_in_Ws=1, max_battery_level_in_Ws=1, charging_rate_in_W=1)
    sat2 = SpacecraftActor("sat2", position=[10000000, 0,0], velocity=[1e-3, -8000, 1e-3], epoch=pk.epoch(0), central_body=earth, battery_level_in_Ws=1, max_battery_level_in_Ws=1, charging_rate_in_W=1)                      

    # init simulation
    sim = paseos.init_sim(sat1)

    # Add satellite 2
    sim.add_known_actor(sat2)

    # Check communication link at == 0. Satellites shall be in line of sight
    remaining_data_in_b, t_w_in_s=sat1.check_communication_link("link1", sat2, 10, 0, 10000)

    assert (t_w_in_s >= 10) and (remaining_data_in_b == 0)

    #Check again after t_w_in_s
    remaining_data_in_b, t_w_in_s=sat1.check_communication_link("link1", sat2, 10, t_w_in_s, 10000)

    assert (remaining_data_in_b == 10000)


if __name__ == "__main__":
    test_communication_link()
