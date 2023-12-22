"""Tests to see if we can create satellites with different devices."""
import numpy as np
import pykep as pk
import sys
import plotly.graph_objects as go
from loguru import logger

sys.path.append("../..")

from paseos import ActorBuilder, SpacecraftActor

from test_utils import get_default_instance


def test_set_TLE():
    """Check if we can set a TLE correctly"""

    _, sentinel2a, earth = get_default_instance()
    # Set the TLE
    line1 = "1 40697U 15028A   23188.15862373  .00000171  00000+0  81941-4 0  9994"
    line2 = "2 40697  98.5695 262.3977 0001349  91.8221 268.3116 14.30817084419867"
    ActorBuilder.set_TLE(sentinel2a, line1, line2)

    # Check that get_altitude returns a sensible value
    earth_radius = 6371000
    assert sentinel2a.get_altitude() > earth_radius + 780000
    assert sentinel2a.get_altitude() < earth_radius + 820000

    # Check that get_position_velocity returns sensible values
    position, velocity = sentinel2a.get_position_velocity(sentinel2a.local_time)
    assert position is not None
    assert velocity is not None

    # Create an actor with a keplerian orbit and check that the position and velocity
    # diverge over time
    s2a_kep = ActorBuilder.get_actor_scaffold("s2a_kep", SpacecraftActor, sentinel2a.local_time)
    ActorBuilder.set_orbit(s2a_kep, position, velocity, sentinel2a.local_time, earth)

    # After some orbits the differences should be significant
    # since the TLE uses SGP4 and the other actor uses Keplerian elements
    t0_later = pk.epoch(sentinel2a.local_time.mjd2000 + 1)
    r, v = sentinel2a.get_position_velocity(t0_later)
    r_kep, v_kep = s2a_kep.get_position_velocity(t0_later)
    print("r,v SGP4 after  1 day")
    print(r)
    print(v)
    print("r,v Kep  after  1 day")
    print(r_kep)
    print(v_kep)
    print("Differences in r and v")
    print(np.linalg.norm(np.array(r) - np.array(r_kep)))
    print(np.linalg.norm(np.array(v) - np.array(v_kep)))
    assert np.linalg.norm(np.array(r) - np.array(r_kep)) > 100000
    assert np.linalg.norm(np.array(v) - np.array(v_kep)) > 400


def test_set_orbit():
    """Check if we can specify an orbit correctly"""
    _, sat1, earth = get_default_instance()
    ActorBuilder.set_orbit(sat1, [1000000, 0, 0], [0, 8000.0, 0], pk.epoch(0), earth)

    # check initial positions
    # r - position vector, v - velocity vector
    r, v = sat1.get_position_velocity(pk.epoch(0))
    assert np.isclose(r[0], 1000000)
    assert np.isclose(r[1], 0)
    assert np.isclose(r[2], 0)
    assert np.isclose(v[0], 0)
    assert np.isclose(v[1], 8000.0)
    assert np.isclose(v[2], 0)

    # check positions one second later
    r, v = sat1.get_position_velocity(pk.epoch(1 * pk.SEC2DAY))
    assert np.isclose(r[0], 999800.6897266058)
    assert np.isclose(r[1], 7999.468463301808)
    assert np.isclose(r[2], 0.0)
    assert np.isclose(v[0], -398.64065398803876)
    assert np.isclose(v[1], 7998.405250997527)
    assert np.isclose(v[2], 0.0)


def test_add_power_devices():
    """Check if we can add a power device"""
    _, sat1, _ = get_default_instance()
    ActorBuilder.set_power_devices(sat1, 42, 42, 42)
    assert sat1.battery_level_in_Ws == 42
    assert sat1.state_of_charge == 1
    assert sat1.charging_rate_in_W == 42


def test_add_comm_device():
    """Check if we can add a comm device"""
    _, sat1, _ = get_default_instance()
    ActorBuilder.add_comm_device(sat1, "dev1", 10)
    ActorBuilder.add_comm_device(sat1, "dev2", 42)

    assert len(sat1.communication_devices) == 2
    assert sat1.communication_devices["dev1"].bandwidth_in_kbps == 10
    assert sat1.communication_devices["dev2"].bandwidth_in_kbps == 42


def test_set_geometric_model():
    """Check if we can set the geometry, and if the moments of inertia are calculated correctly"""
    _, sat1, _ = get_default_instance()
    ActorBuilder.set_cuboid_geometric_model(sat1, mass=100, height=0.5, length=0.5, width=0.5)

    assert sat1.mass == 100
    assert round(sat1._moi[0,0],3) == 4.167      # Value for a h,w,l of each 0.5
    assert sat1._moi[0,1] == 0.0                   # Should be zero if the mass distribution is even

def test_view_geometric_model():
    """Provide a visualisation of the imported geometric model, and test if the cg is in the correct location
    """
    _, sat1, _ = get_default_instance()
    ActorBuilder.set_geometric_model_from_import(sat1,mass=100,file_name='20265_Hexagonal_prism_v1') # test only runs
    # if '../../' is added to start of the file name in geometric_model.pu
    assert np.all(np.round(sat1._center_of_gravity, decimals=0) == np.array([0, 0, 6]))
    # Create trace for the mesh and axis
    mesh = sat1._mesh
    mesh_trace = go.Mesh3d(x=mesh.vertices[:, 0], y=mesh.vertices[:, 1], z=mesh.vertices[:, 2],
                           i=mesh.faces[:, 0], j=mesh.faces[:, 1], k=mesh.faces[:, 2],
                           color='lightblue', opacity=0.5)
    axis_length = 5  # Length of the axes
    axis_end = [[0, 0, 0], [axis_length, 0, 0]], [[0, 0, 0], [0, axis_length, 0]], [[0, 0, 0], [0, 0, axis_length]]
    axis_traces = [go.Scatter3d(x=[end[0][0], end[1][0]], y=[end[0][1], end[1][1]], z=[end[0][2], end[1][2]],
                                marker=dict(color=col), line=dict(color=col, width=4), name=lab)
                   for end, col, lab in zip(axis_end, ['red', 'green', 'blue'], ['X-axis', 'Y-axis', 'Z-axis'])]
    point_coordinates = sat1._center_of_gravity

    # Create a trace for the single point
    point_trace = go.Scatter3d(x=[point_coordinates[0]], y=[point_coordinates[1]], z=[point_coordinates[2]],
                               mode='markers', marker=dict(size=10, color='orange'), name='Center of Gravity')
    fig = go.Figure(data=[mesh_trace] + axis_traces + [point_trace])
    fig.update_layout(scene=dict(aspectmode='data'))
    fig.show()


test1 = test_view_geometric_model()