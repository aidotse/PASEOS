import sys
sys.path.append("../..")

from paseos import ActorBuilder, SpacecraftActor
from paseos.visualization.space_animation import SpaceAnimation


import pykep as pk
import matplotlib.pyplot as plt
from utils import test_setup


def interactive_plot():
    sim, sat1, sat2, sat3 = test_setup()
    ActorBuilder.add_comm_device(sat1, "com_dev", 1)

    sat4 = ActorBuilder.get_actor_scaffold(
        "sat4", SpacecraftActor, [0, -8000000, -10000000], pk.epoch(0)
    )
    ActorBuilder.set_orbit(
        sat4, [0, -8000000, 0], [0, 0, -8000.0], pk.epoch(0), pk.planet.jpl_lp("earth")
    )
    ActorBuilder.set_power_devices(sat4, 7500, 10000, 1)

    anim = SpaceAnimation(sim)

    dt = 100 # time step in seconds
    for t in range(100):
        if t == 25:
            sim.add_known_actor(sat4)
        if t == 50:
            sim.remove_known_actor(sat2.name)
        if t == 75:
            sim.remove_known_actor(sat3.name)
        anim.animate(sim, dt)
        plt.pause(0.05)
    plt.show()


if __name__ == "__main__":
    interactive_plot()
