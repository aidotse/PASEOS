import sys

sys.path.append("../..")

import paseos
from paseos.visualization.space_animation import SpaceAnimation
from paseos.actors.spacecraft_actor import SpacecraftActor
from paseos.actors.actor_builder import ActorBuilder
import pykep as pk
from loguru import logger


def interactive_plot():
    """Animate two satellites in orbit around earth in interactive mode"""
    logger.remove()
    logger.add(sys.stderr, level="INFO")  # using DEBUG level will create tons of text

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
    sim.add_known_actor(sat2)

    sat3 = ActorBuilder.get_actor_scaffold(
        "sat3", SpacecraftActor, [0, -10000000, 0], pk.epoch(0)
    )
    ActorBuilder.set_orbit(sat3, [0, -10000000, 0], [0, 0, 8000.0], pk.epoch(0), earth)
    sim.add_known_actor(sat3)

    anim = SpaceAnimation(sim)

    dt = 300  # time step in seconds
    for t in range(400):
        anim.animate(sim, dt)
        plt.pause(0.01)


if __name__ == "__main__":
    interactive_plot()
