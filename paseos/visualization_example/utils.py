from paseos import ActorBuilder, SpacecraftActor
import paseos

import pykep as pk


def test_setup():
    # Define central body
    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold(
        "sat1", SpacecraftActor, [10000000, 0, 0], pk.epoch(0)
    )
    ActorBuilder.set_orbit(sat1, [10000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_power_devices(sat1, 500, 10000, 1)
    # init simulation
    sim = paseos.init_sim(sat1)

    sat2 = ActorBuilder.get_actor_scaffold(
        "sat2", SpacecraftActor, [10000000, 0, 0], pk.epoch(0)
    )
    ActorBuilder.set_orbit(sat2, [0, 10000000, 0], [0, 0, 8000.0], pk.epoch(0), earth)
    ActorBuilder.set_power_devices(sat2, 5000, 10000, 1)
    sim.add_known_actor(sat2)

    sat3 = ActorBuilder.get_actor_scaffold(
        "sat3", SpacecraftActor, [10000000, 0, 0], pk.epoch(0)
    )
    ActorBuilder.set_orbit(sat3, [0, -10000000, 0], [0, 0, -8000.0], pk.epoch(0), earth)
    ActorBuilder.set_power_devices(sat3, 7500, 10000, 1)
    sim.add_known_actor(sat3)

    return sim, sat1, sat2, sat3
