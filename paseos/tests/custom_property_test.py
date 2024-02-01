"""This test checks whether power charging is performed correctly"""

from test_utils import get_default_instance

import paseos
from paseos import ActorBuilder, SpacecraftActor

import pykep as pk
import numpy as np


def test_custom_power_consumption_property():
    """Checks whether we can create a custom property to track power consumption of an actor"""

    # Initialize the actor
    sim, sat1, earth = get_default_instance()
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [10000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_power_devices(
        sat1, 50000, 1000000, 1, paseos.PowerDeviceType.SolarPanel
    )

    # Add a custom property which tracks the total power consumption
    prop_name = "total_power_consumption"

    # Define the update function
    def prop_update_fn(actor, dt, power_consumption):
        return actor.get_custom_property(prop_name) + power_consumption * dt

    ActorBuilder.add_custom_property(
        actor=sat1,
        property_name=prop_name,
        update_function=prop_update_fn,
        initial_value=0,
    )
    print(f"Actor custom properties are now {sat1.custom_properties}")

    # init simulation
    sim = paseos.init_sim(sat1)

    # simulate a bit
    sim.advance_time(100, 10)

    # check consumed power
    assert np.isclose(sat1.get_custom_property(prop_name), 100 * 10)

    # check set function
    sat1.set_custom_property(prop_name, 0)
    assert sat1.get_custom_property(prop_name) == 0

    # check quantity is tracked by operations monitor
    sim.monitor[prop_name]
    sim.monitor.plot(prop_name)
    sim.save_status_log_csv("test.csv")
