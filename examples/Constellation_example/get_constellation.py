"""The code is this files generates position and velocities for a constelation"""

import numpy as np
import pykep as pk


def get_constellation(altitude, inclination, nSats, nPlanes, t0):
    """Creates a constellation with the passed parameters

    Args:
        altitude (float): Altitude in meters.
        inclination (float): Inclination in degree.
        nSats (int): Number of sats per plane.
        nPlanes (int): Number of orbital planes.
        t0 (pk.epoch): Initial time.

    Returns:
        planets,satellites: pykep planets and list of (r,v) of the constellation.
    """
    # Inspired by https://github.com/esa/LADDS/blob/main/notebooks/ConstellationGeneration/ConstellationGeneration.ipynb
    # ---extra-params----------------------------------------------------------------------------------------------------

    # offsetM = offset for Mean Anomaly added after each plane (relative phasing)
    # walker constellation: offsetM = F * 360 / (nPlanes * nSats) ; F element {0, ... , nPlanes - 1}
    offsetM = 0  # default 0

    # argPeriapsis = argument of periapsis
    # starting point of satellite placement for each plane
    # argPeriapsis = pi avoids collisions in planes that intersect at reference plane
    argPeriapsis = np.pi  # default np.pi

    # startingW = offset for W that is not accumulating (W = longitude of ascending node)
    # formula for overlapping shells (same altitude, same inclination):
    # (360 / G) / 2 ; G = smallest common multiple of the overlapping nPlanes
    startingW = 0  # default 0

    # W_area: orbital planes are distributed evenly within range [startingW,startingW + maximumW)
    W_area = 360  # default 360
    # -------------------------------------------------------------------------------------------------------------------

    minW = startingW

    a = altitude + 6371000  # in [m], earth radius included
    e = 0
    i = inclination * pk.DEG2RAD
    W = pk.DEG2RAD * minW
    w = argPeriapsis * pk.DEG2RAD
    M = 0

    plane_count = 0

    mu_central_body = pk.MU_EARTH
    mu_self = 1
    radius = 1
    safe_radius = 1

    pStep = pk.DEG2RAD * W_area / nPlanes  # W goes from startingW to startingW+W_area
    sStep = 2 * np.pi / nSats  # M goes from 0° to 360°
    sExtraStep = pk.DEG2RAD * offsetM

    planet_list = []
    elements_list = []
    for x in range(nPlanes):
        for y in range(nSats):
            planet_list.append(
                pk.planet.keplerian(
                    t0,
                    [a, e, i, W, w, M],
                    mu_central_body,
                    mu_self,
                    radius,
                    safe_radius,
                    "sat",
                )
            )
            elements_list.append([a, e, i, W, w, M])
            M = M + sStep
        plane_count = plane_count + 1
        W = W + pStep
        M = plane_count * sExtraStep  # equals 0 + count*0 = 0 in the usual case

    print("Created " + str(len(elements_list)) + " satellites...")

    print("Computing constellation's positions and velocities...")
    satellites = []
    for elements in elements_list:
        pos, v = pk.par2ic(elements, pk.MU_EARTH)

        # convert to numpy
        pos = np.asarray(pos)
        v = np.asarray(v)

        satellites.append((pos, v))

    print("Done!")
    return planet_list, satellites
