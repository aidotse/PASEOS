import pykep as pk
import sys

sys.path.append("../..")
import paseos
from paseos.utils.load_default_cfg import load_default_cfg

from paseos import (
    SpacecraftActor,
    GroundstationActor,
    ActorBuilder,
    find_next_window,
)

import numpy as np


def setup_sentinel_example(t0):
    """Sets up the example with sentinel2B and maspolamas ground station."""
    """Tests the find_next_window function"""
    earth = pk.planet.jpl_lp("earth")

    # Define Sentinel 2 orbit
    sentinel2B = ActorBuilder.get_actor_scaffold("Sentinel2B", SpacecraftActor, t0)
    sentinel2B_line1 = "1 40697U 15028A   23193.19358829  .00000126  00000-0  64636-4 0  9993"
    sentinel2B_line2 = "2 40697  98.5693 267.3615 0001325  90.2705 269.8630 14.30818726420585"
    s2b = pk.planet.tle(sentinel2B_line1, sentinel2B_line2)

    # Calculating S2B ephemerides.
    sentinel2B_eph = s2b.eph(t0)

    ActorBuilder.set_orbit(
        actor=sentinel2B,
        position=sentinel2B_eph[0],
        velocity=sentinel2B_eph[1],
        epoch=t0,
        central_body=earth,
    )

    # sentinel2B.set_central_body_shape(Sphere([0, 0, 0], _PASEOS_TESTS_EARTH_RADIUS))

    # Define ground station
    maspalomas_groundstation = ActorBuilder.get_actor_scaffold(
        name="maspalomas_groundstation", actor_type=GroundstationActor, epoch=t0
    )

    ActorBuilder.set_ground_station_location(
        maspalomas_groundstation, 27.7629, -15.6338, 205.1, minimum_altitude_angle=5
    )

    # Add communication link
    ActorBuilder.add_comm_device(sentinel2B, device_name="link1", bandwidth_in_kbps=1)
    return sentinel2B, maspalomas_groundstation


def main():
    t0 = pk.epoch_from_string("2019-02-25 08:40:17.000")
    sentinel2B, maspalomas_groundstation = setup_sentinel_example(t0)
    cfg = load_default_cfg()  # loading cfg to modify defaults
    cfg.sim.start_time = t0.mjd2000 * pk.DAY2SEC  # convert epoch to seconds
    sim = paseos.init_sim(sentinel2B, cfg)

    lengths = []
    starts = []
    n = 4
    while n:
        start, length, _ = find_next_window(
            sentinel2B,
            local_actor_communication_link_name="link1",
            target_actor=maspalomas_groundstation,
            search_window_in_s=3600,
            t0=sentinel2B.local_time,
        )
        if start is not None:
            if len(starts) != 0:
                if not (start in starts):
                    lengths.append(length)
                    starts.append(start)
                    print("n: ", n)
                    n -= 1
                    n_sec_advance = (
                        start.mjd2000 * pk.DAY2SEC
                        - sentinel2B.local_time.mjd2000 * pk.DAY2SEC
                        + length
                    )
                else:
                    n_sec_advance = 500
            else:
                lengths.append(length)
                starts.append(start)
                print("n: ", n)
                n -= 1
                n_sec_advance = (
                    start.mjd2000 * pk.DAY2SEC - sentinel2B.local_time.mjd2000 * pk.DAY2SEC + length
                )
        else:
            n_sec_advance = 500

        sim.advance_time(n_sec_advance, 0)
        print(sentinel2B.local_time)

    print("Lengths: ", lengths)
    print("Starts: ", starts)
    lengths_expected = np.array([31032 - 30426, 37026 - 36321, 75297 - 74811, 81396 - 80661])
    errors = np.abs(lengths_expected - np.array(lengths))
    errors_percentage = errors / np.array(lengths)
    print("Error percentages: ", errors_percentage)
    print("Mean percentage error: ", np.mean(errors_percentage))


if __name__ == "__main__":
    print("START")
    main()
