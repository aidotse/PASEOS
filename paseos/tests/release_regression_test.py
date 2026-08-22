"""Regression tests for bugs found while validating the 0.2.1 release."""

import pykep as pk
import pytest
from test_utils import get_default_instance

import paseos
from paseos import ActorBuilder, SpacecraftActor, load_default_cfg


def test_perform_activity_twice_in_a_row():
    """Two consecutive perform_activity calls have to work.

    asyncio.run() unsets the current event loop, so the previous
    asyncio.get_event_loop() lookup raised RuntimeError on the second call
    from Python 3.10 onwards. Only reproduces on 3.10+, hence the conda CI job.
    """
    sim, _, _ = get_default_instance()

    results = []

    async def func(args):
        results.append(1)

    sim.register_activity("Testing", activity_function=func, power_consumption_in_watt=10)

    sim.perform_activity("Testing")
    sim.perform_activity("Testing")

    assert len(results) == 2, "Both activity runs should have executed."


def test_logging_interval_is_respected():
    """The status log has to fire at the configured interval, not a multiple of it."""
    earth = pk.planet.jpl_lp("earth")
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [10000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_power_devices(sat1, 500, 10000, 1)

    cfg = load_default_cfg()
    cfg.sim.start_time = 0.0
    cfg.sim.dt = 10.0
    cfg.io.logging_interval = 10.0
    sim = paseos.init_sim(sat1, cfg)

    sim.advance_time(100.0, 0)

    # Compared with a tolerance: the simulation time accumulates dt step by step,
    # so exact equality would trip over float representation.
    # Before the fix this logged at 10, 40, 70, 100 -- every 30s.
    timesteps = sim.monitor["timesteps"]
    assert timesteps == pytest.approx([10, 20, 30, 40, 50, 60, 70, 80, 90, 100]), (
        f"Expected a log every 10s but got {timesteps}"
    )
