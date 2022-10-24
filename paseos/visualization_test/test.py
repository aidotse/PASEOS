import sys

sys.path.append("../..")

from paseos import ActorBuilder, SpacecraftActor
from paseos.visualization.space_animation import SpaceAnimation
import paseos

import pykep as pk
import matplotlib.pyplot as plt


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


def test_animation():
    sim = test_setup()
    anim = SpaceAnimation(sim)
    anim.animate(sim, "paseos_test", 200, 400)


def test_live_visuals():
    sim, sat1, sat2, sat3 = test_setup()

    sat4 = ActorBuilder.get_actor_scaffold(
        "sat4", SpacecraftActor, [0, -8000000, -10000000], pk.epoch(0)
    )
    ActorBuilder.set_orbit(
        sat4, [0, -8000000, 0], [0, 0, -8000.0], pk.epoch(0), pk.planet.jpl_lp("earth")
    )
    ActorBuilder.set_power_devices(sat4, 7500, 10000, 1)

    anim = SpaceAnimation(sim)

    dt = 100
    for t in range(100):
        sim.advance_time(dt)
        if t == 25:
            sim.add_known_actor(sat4)
        if t == 50:
            sim.remove_known_actor(sat2.name)
        if t == 75:
            sim.remove_known_actor(sat3.name)
        anim.update(sim)
        plt.pause(0.05)
    plt.show()


if __name__ == "__main__":
    test_live_visuals()
