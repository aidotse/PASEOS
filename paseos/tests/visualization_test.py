"""Tests to check visualization."""
import sys

sys.path.append("../..")
from paseos import ActorBuilder, SpacecraftActor
from paseos.visualization.space_animation import SpaceAnimation
from test_utils import get_default_instance
import pykep as pk


def test_animation():
    """Simple test to verify that the animation executes without errors."""
    sim, sat1, earth = get_default_instance()

    sat2 = ActorBuilder.get_actor_scaffold("sat2", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat2, [0, 10000000, 0], [0, 0, 8000.0], pk.epoch(0), earth)
    ActorBuilder.set_power_devices(sat2, 5000, 10000, 1)
    sim.add_known_actor(sat2)

    anim = SpaceAnimation(sim)

    dt = 100
    for t in range(10):
        anim.animate(sim, dt)


if __name__ == "__main__":
    test_animation()
