"""Test using a mesh for the central body."""

import numpy as np
import pickle
import pykep as pk

from paseos import ActorBuilder, SpacecraftActor
import paseos

mesh_path = "paseos/tests/test_data/67P_low_poly.pk"

# Orbital elements / ephemeris for 67P
# from https://en.wikipedia.org/wiki/67P/Churyumov%E2%80%93Gerasimenko
epoch = pk.epoch(2460000.5, "jd")
a = 3.457 * pk.AU
e = 0.64989
i = 3.8719 * pk.DEG2RAD
W = 36.33 * pk.DEG2RAD
w = 22.15 * pk.DEG2RAD
M = 73.57 * pk.DEG2RAD
# We overestimate MU due to a bug in pykep
# https://github.com/esa/pykep/issues/167
# MU = 666.19868
MU = 2e4


def test_mesh_for_central_body():
    """Checks if we can create an actor with a mesh for the central body."""

    paseos.set_log_level("TRACE")

    # Create a planet object from pykep for 67P
    comet = pk.planet.keplerian(epoch, (a, e, i, W, w, M), pk.MU_SUN, MU, 4000, 4000, "67P")

    # Load the 67P mesh with pickle
    with open(mesh_path, "rb") as f:
        mesh_points, mesh_triangles = pickle.load(f)
        mesh_points = np.array(mesh_points)
        mesh_triangles = np.array(mesh_triangles)

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, epoch=epoch)

    # Set a keplerian orbit around 67P
    # Note that keplerian is not very realistic for 67P, just for testing
    ActorBuilder.set_orbit(sat1, [8000, 0, 0], [0.0, 2.0, 0.0], epoch, comet)

    # Set the mesh and create some more satellites around 67P
    ActorBuilder.set_central_body(sat1, comet, (mesh_points, mesh_triangles))

    sat2 = ActorBuilder.get_actor_scaffold("sat2", SpacecraftActor, epoch=epoch)
    ActorBuilder.set_orbit(sat2, [-8000, 1e-8, 1e-8], [0, -2.0, 0], epoch, comet)
    ActorBuilder.set_central_body(sat2, comet, (mesh_points, mesh_triangles))

    sat3 = ActorBuilder.get_actor_scaffold("sat3", SpacecraftActor, epoch=epoch)
    ActorBuilder.set_orbit(sat3, [1e-8, 8000, 1e-8], [-2.0, 0, 0], epoch, comet)
    ActorBuilder.set_central_body(sat3, comet, (mesh_points, mesh_triangles))

    sat4 = ActorBuilder.get_actor_scaffold("sat4", SpacecraftActor, epoch=epoch)
    ActorBuilder.set_orbit(sat4, [1e-8, -8000, 1e-8], [2.0, 0, 0], epoch, comet)
    ActorBuilder.set_central_body(sat4, comet, (mesh_points, mesh_triangles))

    # init simulation
    sim = paseos.init_sim(sat1, starting_epoch=epoch)

    sim.add_known_actor(sat2)
    sim.add_known_actor(sat3)
    sim.add_known_actor(sat4)

    # Write a plot to file, for debugging
    paseos.plot(sim, paseos.PlotType.SpacePlot, "mesh_test.png")
