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
MU = 1e5

plot = False


def get_default_setup():
    paseos.set_log_level("INFO")

    # Create a planet object from pykep for 67P
    comet = pk.planet.keplerian(epoch, (a, e, i, W, w, M), pk.MU_SUN, MU, 2000, 2000, "67P")

    # Load the 67P mesh with pickle
    with open(mesh_path, "rb") as f:
        mesh_points, mesh_triangles = pickle.load(f)
        # The mesh file for the test is normalized to -1,1
        # Thus we convert back to meters
        mesh_points = np.array(mesh_points) * 3126.6064453124995
        mesh_triangles = np.array(mesh_triangles)

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, epoch=epoch)

    # Set a keplerian orbit around 67P
    # Note that keplerian is not very realistic for 67P, just for testing
    ActorBuilder.set_orbit(sat1, [4000, 1, 1], [0.0, 5, 0.0], epoch, comet)

    # Set the mesh and create some more satellites around 67P
    ActorBuilder.set_central_body(sat1, comet, (mesh_points, mesh_triangles))

    # init simulation
    sim = paseos.init_sim(sat1, starting_epoch=epoch)

    return sim, sat1, comet, mesh_points, mesh_triangles


def test_mesh_for_central_body():
    """Checks if we can create an actor with a mesh for the central body."""

    _, _, _, _, _ = get_default_setup()


def test_mesh_los():
    """Checks if we can compute line of sight using a mesh for the central body."""

    sim, sat1, comet, mesh_points, mesh_triangles = get_default_setup()

    sat2 = ActorBuilder.get_actor_scaffold("sat2", SpacecraftActor, epoch=epoch)
    ActorBuilder.set_orbit(sat2, [-4000, 1, 1], [5, 0, 0], epoch, comet)
    ActorBuilder.set_central_body(sat2, comet, (mesh_points, mesh_triangles))

    sat3 = ActorBuilder.get_actor_scaffold("sat3", SpacecraftActor, epoch=epoch)
    ActorBuilder.set_orbit(sat3, [1, 4000, 1], [-5, 0, 0], epoch, comet)
    ActorBuilder.set_central_body(sat3, comet, (mesh_points, mesh_triangles))

    sat4 = ActorBuilder.get_actor_scaffold("sat4", SpacecraftActor, epoch=epoch)
    ActorBuilder.set_orbit(sat4, [1, -4000, 1], [0, -5, 0], epoch, comet)
    ActorBuilder.set_central_body(sat4, comet, (mesh_points, mesh_triangles))

    sat5 = ActorBuilder.get_actor_scaffold("sat5", SpacecraftActor, epoch=epoch)
    ActorBuilder.set_orbit(sat5, [1, 1, 4000], [5, 0, 0], epoch, comet)
    ActorBuilder.set_central_body(sat5, comet, (mesh_points, mesh_triangles))

    sat6 = ActorBuilder.get_actor_scaffold("sat6", SpacecraftActor, epoch=epoch)
    ActorBuilder.set_orbit(sat6, [1, 1, -4000], [-5, 0, 0], epoch, comet)
    ActorBuilder.set_central_body(sat6, comet, (mesh_points, mesh_triangles))

    sim.add_known_actor(sat2)
    sim.add_known_actor(sat3)
    sim.add_known_actor(sat4)
    sim.add_known_actor(sat5)
    sim.add_known_actor(sat6)

    assert not sat1.is_in_line_of_sight(sat2, epoch)
    assert not sat3.is_in_line_of_sight(sat4, epoch)
    assert not sat5.is_in_line_of_sight(sat6, epoch)

    assert sat1.is_in_line_of_sight(sat3, epoch)
    assert sat1.is_in_line_of_sight(sat4, epoch)
    assert sat1.is_in_line_of_sight(sat5, epoch)
    assert sat1.is_in_line_of_sight(sat6, epoch)

    assert sat2.is_in_line_of_sight(sat3, epoch)
    assert sat2.is_in_line_of_sight(sat4, epoch)
    assert sat2.is_in_line_of_sight(sat5, epoch)
    assert sat2.is_in_line_of_sight(sat6, epoch)

    assert sat3.is_in_line_of_sight(sat5, epoch)
    assert sat3.is_in_line_of_sight(sat6, epoch)

    assert sat4.is_in_line_of_sight(sat5, epoch)
    assert sat4.is_in_line_of_sight(sat6, epoch)

    # Write a plot to file, for debugging
    if plot:
        paseos.plot(sim, paseos.PlotType.SpacePlot, "results/mesh_test.png")

    # Propagate for a bit, just to check we can
    sim.advance_time(600, 0)


def test_mesh_eclipse():
    """Checks if we can compute eclipse correctly using a mesh for the central body."""
    sim, sat1, _, _, _ = get_default_setup()

    # Add a power device
    ActorBuilder.set_power_devices(
        actor=sat1,
        battery_level_in_Ws=500,
        max_battery_level_in_Ws=1000,
        charging_rate_in_W=10,
    )

    assert not sat1.is_in_eclipse(epoch)
    assert sat1.battery_level_in_Ws == 500
    if plot:
        paseos.plot(sim, paseos.PlotType.SpacePlot, "results/mesh_test_no_eclipse.png")

    # Advance time and consume power we are generating
    sim.advance_time(2260, 10)

    assert sat1.is_in_eclipse()
    assert np.isclose(sat1.battery_level_in_Ws, 400)
    if plot:
        paseos.plot(sim, paseos.PlotType.SpacePlot, "results/mesh_test_eclipse.png")


def test_mesh_rotation():
    sim, sat1, comet, mesh_points, mesh_triangles = get_default_setup()

    # Set a rotation period of 1 second around the z axis
    ActorBuilder.set_central_body(
        sat1,
        comet,
        (mesh_points, mesh_triangles),
        rotation_declination=90,
        rotation_right_ascension=0,
        rotation_period=1,
    )

    # Epochs after a quarter and half rotation
    epoch_quarter = pk.epoch(epoch.mjd2000 + 0.25 * pk.SEC2DAY, "mjd2000")
    epoch_half = pk.epoch(epoch.mjd2000 + 0.5 * pk.SEC2DAY, "mjd2000")

    central_body = sat1.central_body

    # NOTE the we move the points in the opposite direction of the rotation
    # to avoid rotating the mesh
    rotate_p = central_body._apply_rotation([1, 0, 0], epoch_quarter)
    assert all(np.isclose(rotate_p, [0, -1, 0], atol=1e-6))

    rotate_p = central_body._apply_rotation([0, 1, 0], epoch_quarter)
    assert all(np.isclose(rotate_p, [1, 0, 0], atol=1e-6))

    rotate_p = central_body._apply_rotation([0, -1, 0], epoch_quarter)
    assert all(np.isclose(rotate_p, [-1, 0, 0], atol=1e-6))

    rotate_p = central_body._apply_rotation([0, 1, 0], epoch_half)
    assert all(np.isclose(rotate_p, [0, -1, 0], atol=1e-6))

    rotate_p = central_body._apply_rotation([-1, 0, 0], epoch_half)
    assert all(np.isclose(rotate_p, [1, 0, 0], atol=1e-6))

    rotate_p = central_body._apply_rotation([0, 0, 1], epoch_quarter)
    assert all(np.isclose(rotate_p, [0, 0, 1], atol=1e-6))

    rotate_p = central_body._apply_rotation([0, 0, -1], epoch_half)
    assert all(np.isclose(rotate_p, [0, 0, -1], atol=1e-6))

    # Set a rotation period of 2 second around the y axis
    ActorBuilder.set_central_body(
        sat1,
        comet,
        (mesh_points, mesh_triangles),
        rotation_declination=0,
        rotation_right_ascension=90,
        rotation_period=2,
    )

    # Epochs after a quarter and half rotation
    epoch_quarter = pk.epoch(epoch.mjd2000 + 0.5 * pk.SEC2DAY, "mjd2000")
    epoch_half = pk.epoch(epoch.mjd2000 + 1 * pk.SEC2DAY, "mjd2000")

    central_body = sat1.central_body

    # NOTE the we move the points in the opposite direction of the rotation
    # to avoid rotating the mesh
    rotate_p = central_body._apply_rotation([1, 0, 0], epoch_quarter)
    assert all(np.isclose(rotate_p, [0, 0, 1], atol=1e-6))

    rotate_p = central_body._apply_rotation([0, 0, -1], epoch_quarter)
    assert all(np.isclose(rotate_p, [1, 0, 0], atol=1e-6))

    rotate_p = central_body._apply_rotation([0, 0, 1], epoch_quarter)
    assert all(np.isclose(rotate_p, [-1, 0, 0], atol=1e-6))

    rotate_p = central_body._apply_rotation([0, 0, 1], epoch_half)
    assert all(np.isclose(rotate_p, [0, 0, -1], atol=1e-6))

    rotate_p = central_body._apply_rotation([-1, 0, 0], epoch_half)
    assert all(np.isclose(rotate_p, [1, 0, 0], atol=1e-6))

    rotate_p = central_body._apply_rotation([0, 1, 0], epoch_quarter)
    assert all(np.isclose(rotate_p, [0, 1, 0], atol=1e-6))

    rotate_p = central_body._apply_rotation([0, -1, 0], epoch_half)
    assert all(np.isclose(rotate_p, [0, -1, 0], atol=1e-6))
