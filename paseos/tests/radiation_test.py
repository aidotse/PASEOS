"""This test checks whether power charging is performed correctly"""
import asyncio

import numpy as np
import pytest

from test_utils import get_default_instance, wait_for_activity
from paseos.radiation.radiation_model import RadiationModel
from paseos import ActorBuilder
import paseos


def test_radiation_model():
    paseos.set_log_level("TRACE")

    # Has to be seeded for reproducibility
    np.random.seed(42)

    # Set up radiation model
    rm = RadiationModel(1e-5, 1e-7, 1e-9)

    # Test data corruption model
    mask = rm.model_data_corruption([10, 4, 8], 1e5)
    assert mask.shape == (10, 4, 8)
    assert mask.sum() == 199

    # Test device restarts and failures
    np.random.seed(42)
    assert not rm.did_device_restart(1e5)
    assert not rm.did_device_restart(1e7)
    assert rm.did_device_restart(1e9)

    np.random.seed(42)
    assert not rm.did_device_experience_failure(1e7)
    assert not rm.did_device_experience_failure(1e9)
    assert rm.did_device_experience_failure(1e11)


@pytest.mark.asyncio
async def test_radiation_model_data_corruption():
    """Checks whether we can charge an actor"""
    sim, sat1, earth = get_default_instance()
    paseos.set_log_level("INFO")

    # Has to be seeded for reproducibility
    np.random.seed(42)

    # Setup radiation model example where actor is interrupted
    ActorBuilder.set_radiation_model(
        actor=sat1,
        data_corruption_events_per_s=1e-5,
        restart_events_per_s=0,
        failure_events_per_s=0,
    )

    mask = sim.model_data_corruption([10, 4, 8], 1e5)
    assert mask.shape == (10, 4, 8)
    assert mask.sum() == 199


@pytest.mark.asyncio
async def test_radiation_model_device_death():
    """Checks whether we can charge an actor"""
    sim, sat1, earth = get_default_instance()
    paseos.set_log_level("INFO")

    # Has to be seeded for reproducibility
    np.random.seed(42)

    # Setup radiation model example where actor is interrupted
    ActorBuilder.set_radiation_model(
        actor=sat1,
        data_corruption_events_per_s=0,
        restart_events_per_s=0,
        failure_events_per_s=100,
    )

    async def func(args):
        await asyncio.sleep(1.0)

    # Register an activity that draws 10 watt per second
    sim.register_activity("Testing", activity_function=func, power_consumption_in_watt=0)

    # Run the activity
    sim.perform_activity("Testing")
    await wait_for_activity(sim)

    # Check sat1 died.
    assert sat1.is_dead


@pytest.mark.asyncio
async def test_radiation_model_interruption():
    """Checks whether we can charge an actor"""
    sim, sat1, earth = get_default_instance()
    paseos.set_log_level("INFO")

    # Has to be seeded for reproducibility
    np.random.seed(42)

    # Setup radiation model example where actor is interrupted
    ActorBuilder.set_radiation_model(
        actor=sat1,
        data_corruption_events_per_s=0,
        restart_events_per_s=1,
        failure_events_per_s=0,
    )

    # Out test case is a function that increments a value, genius.
    # (needs a list to increase the actual value by reference and not create a copy)
    test_val = [0]

    async def func(args):
        for _ in range(10):
            args[0][0] += 1
            await asyncio.sleep(0.2)

    # Register an activity that draws 10 watt per second
    sim.register_activity("Testing", activity_function=func, power_consumption_in_watt=0)

    # Run the activity
    sim.perform_activity("Testing", activity_func_args=[test_val])
    await wait_for_activity(sim)

    # Check activity result, exact result is runtime dependent.
    assert test_val[0] > 4 and test_val[0] < 8
    assert not sat1.is_dead
