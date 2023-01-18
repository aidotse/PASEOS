"""Utility for tests"""
import sys
import asyncio

sys.path.append("../..")

import paseos
from paseos import ActorBuilder, SpacecraftActor

import pykep as pk


def get_default_instance() -> (paseos.PASEOS, SpacecraftActor, pk.planet):
    """Sets up a instance of paseos with a satellite in orbit around Earth"""

    # Define central body
    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [10000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_power_devices(sat1, 500, 10000, 1)
    # init simulation
    sim = paseos.init_sim(sat1)

    return sim, sat1, earth


async def wait_for_activity(sim):
    while sim._is_running_activity is True:
        await asyncio.sleep(0.1)
