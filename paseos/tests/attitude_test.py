import numpy as np
import pykep as pk
import sys

sys.path.append("../..")
import paseos
from paseos import ActorBuilder, SpacecraftActor, load_default_cfg


def gravity_disturbance_cube_test():
    """This test checks whether a 3-axis symmetric, uniform body (a cube with constant density, and cg at origin)
    creates no angular acceleration/velocity due to gravity"""
    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [7000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_geometric_model(sat1, mass=100)
    ActorBuilder.set_attitude_model(sat1)
    ActorBuilder.set_disturbances(sat1, gravitational=True)

    # init simulation
    sim = paseos.init_sim(sat1)

    # Check initial conditions
    assert np.all(sat1._attitude_model._actor_angular_velocity == 0.0)

    # run simulation for 1 period
    orbital_period = 2 * np.pi * np.sqrt((6371000 + 7000000) ** 3 / 3.986004418e14)
    sim.advance_time(orbital_period, 0)
    nadir = sat1._attitude_model.nadir_vector()

    # check conditions after 1 orbit
    assert np.all(sat1._attitude_model._actor_angular_acceleration == 0.0)

def gravity_disturbance_pole_test():
    """This test checks whether a 2-axis symmetric, uniform body (a pole (10x1x1) with constant density, and cg at
    origin) stabilises in orbit due to gravitational acceleration
    It additionally checks the implementation of custom meshes of the geometric model"""

    vertices = [
                [-5, -0.5, -0.5],
                [-5, -0.5, 0.5],
        [-5, 0.5, -0.5],
        [-5, 0.5, 0.5],
        [5, -0.5, -0.5],
        [5, -0.5, 0.5],
        [5, 0.5, -0.5],
        [5, 0.5, 0.5],
    ]
    faces = [
        [0, 1, 3],
        [0, 3, 2],
        [0, 2, 6],
        [0, 6, 4],
        [1, 5, 3],
        [3, 5, 7],
        [2, 3, 7],
        [2, 7, 6],
        [4, 6, 7],
        [4, 7, 5],
        [0, 4, 1],
        [1, 4, 5],
    ]

    earth = pk.planet.jpl_lp("earth")

    # Define local actor
    sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
    ActorBuilder.set_orbit(sat1, [7000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)
    ActorBuilder.set_geometric_model(sat1, mass=100, vertices=vertices, faces=faces)
    orbital_period = 2 * np.pi * np.sqrt((6371000 + 7000000) ** 3 / 3.986004418e14)
    ActorBuilder.set_attitude_model(sat1)#, actor_initial_angular_velocity=[0,2*np.pi/orbital_period,0])
    ActorBuilder.set_disturbances(sat1, gravitational=True)

    # init simulation
    cfg = load_default_cfg()  # loading cfg to modify defaults
    cfg.sim.dt = 100.0  # setting higher timestep to run things quickly
    sim = paseos.init_sim(sat1, cfg)


    # Check initial conditions
    assert np.all(sat1._attitude_model._actor_attitude_in_rad == 0.0)

    # run simulation for 1 period
    for i in range(11):
        sim.advance_time(orbital_period*0.1, 0)

    # check conditions after 0.1 orbit, satellite should have acceleration around y-axis to align pole towards earth
    assert np.round(sat1._attitude_model._actor_angular_acceleration[0],10) == 0.0
    assert not np.round(sat1._attitude_model._actor_angular_acceleration[1],10) == 0.0

