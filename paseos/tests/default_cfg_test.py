"""Tests whether the default cfg passes validation."""

import pykep as pk

import paseos
from paseos import ActorBuilder, SpacecraftActor, load_default_cfg


def test_default_cfg():
    """Load default cfg and check it."""

    # Need some actor to init paseos
    earth = pk.planet.jpl_lp("earth")
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [10000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)

    cfg = load_default_cfg()
    _ = paseos.init_sim(sat1, cfg)
