"""Test the ability to use a custom propagator in a paseos simulation."""
import sys

sys.path.append("../..")

import numpy as np
import pykep as pk
from paseos import SpacecraftActor, ActorBuilder


def test_custom_propagator():
    """Test if we can just determine position as static with a custom propagator"""

    # Create a spacecraft actor
    starting_epoch = pk.epoch(42)
    my_sat = ActorBuilder.get_actor_scaffold(
        name="my_sat", actor_type=SpacecraftActor, epoch=starting_epoch
    )

    # Define a custom propagator function that just returns a sinus position
    def my_propagator(epoch: pk.epoch):
        """Custom propagator that returns a sinus position"""
        time_since_epoch_in_seconds = (
            epoch.mjd2000 - starting_epoch.mjd2000
        ) * pk.DAY2SEC

        r = [np.sin(time_since_epoch_in_seconds), 0.0, 0.0]
        v = [42.0, 42.0, 42.0]

        return r, v

    # Set the custom propagator
    ActorBuilder.set_custom_orbit(my_sat, my_propagator, starting_epoch)

    # Check that the position is correct
    r = my_sat.get_position(starting_epoch)
    assert np.allclose(r, [0, 0, 0])

    r, v = my_sat.get_position_velocity(starting_epoch)
    assert np.allclose(r, [0, 0, 0])
    assert np.allclose(v, [42, 42, 42])

    # Check that the position is correct at a later time
    later = pk.epoch(42 + 0.5 * np.pi * pk.SEC2DAY)
    r = my_sat.get_position(later)
    assert np.allclose(r, [1, 0, 0])

    r, v = my_sat.get_position_velocity(later)
    assert np.allclose(r, [1, 0, 0])
    assert np.allclose(v, [42, 42, 42])
