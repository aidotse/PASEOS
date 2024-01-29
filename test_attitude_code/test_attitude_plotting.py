# We use pykep for orbit determination
import pykep as pk
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

import paseos
from paseos.actors.spacecraft_actor import SpacecraftActor
from paseos.actors.actor_builder import ActorBuilder

matplotlib.use("Qt5Agg")

# Define central body
earth = pk.planet.jpl_lp("earth")

# Define spacecraft actor
sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
sat2 = ActorBuilder.get_actor_scaffold("sat2", SpacecraftActor, pk.epoch(0))
# geostationary orbit:

lat = 79.6 * np.pi / 180
lon = -71.6 * np.pi / 180

R = 6371000 + 35786000
v = 3074.66

#arr = np.array([-1.24217547e-09, 1.01735657e-07, -3.87201400e-08])
arr = np.array([-3.18159529e-09, 1.02244882e-07, -3.72362170e-08])
initial_magn = np.ndarray.tolist(arr / np.linalg.norm(arr) * 1000)
initial_pointing = np.ndarray.tolist(arr / np.linalg.norm(arr))

ActorBuilder.set_orbit(
    sat1,
    position=[R * np.cos(np.pi / 2 + lon), R * np.sin(np.pi / 2 + lon), 0],
    velocity=[-v * np.sin(np.pi / 2 + lon), v * np.cos(np.pi / 2 + lon), 0],
    epoch=pk.epoch(0),
    central_body=earth,
)
ActorBuilder.set_orbit(
    sat2,
    position=[R * np.cos(np.pi / 2 + lon), R * np.sin(np.pi / 2 + lon), 0],
    velocity=[-v * np.sin(np.pi / 2 + lon), v * np.cos(np.pi / 2 + lon), 0],
    epoch=pk.epoch(0),
    central_body=earth,
)

ActorBuilder.set_geometric_model(sat1, mass=100)
ActorBuilder.set_geometric_model(sat2, mass=100)

ActorBuilder.set_attitude_model(
    sat1,
    actor_initial_angular_velocity=[0.0, 0.0, 0.0],
    actor_pointing_vector_body=initial_pointing,
    actor_initial_attitude_in_rad=[0.0, 0.0, 0.0],
    actor_residual_magnetic_field=initial_magn,
)
ActorBuilder.set_attitude_model(
    sat2,
    actor_initial_angular_velocity=[0.0, 0.0, 0.0],
    actor_pointing_vector_body=initial_pointing,
    actor_initial_attitude_in_rad=[0.0, 0.0, 0.0],
    actor_residual_magnetic_field=[0.0, 0.0, 0.0],
)

# disturbances:
ActorBuilder.set_disturbances(sat1, magnetic=True)
ActorBuilder.set_disturbances(sat2, magnetic=True)


sim = paseos.init_sim(sat1)
sim.add_known_actor(sat2)
plt.close()

pos = []
x = []
y = []
z = []
pointing_vector = []

fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")
for i in range(46):
    print("----------", i, "----------")
    pos = sat1.get_position(sat1.local_time)
    x.append(sat1.get_position(sat1.local_time)[0])
    y.append(sat1.get_position(sat1.local_time)[1])
    z.append(sat1.get_position(sat1.local_time)[2])

    euler = sat1.attitude_in_rad()

    # pointing vector:
    vector = sat1.pointing_vector()
    vector[np.isclose(vector, np.zeros(3))] = 0
    # scale for plotting
    vector = vector * 8e6

    # pointing vector:
    vector2 = sat2.pointing_vector()
    vector2[np.isclose(vector2, np.zeros(3))] = 0
    # scale for plotting
    vector2 = vector2 * 8e6

    # angular velocity vector:
    # normalize first:
    ang_vel = sat1.angular_velocity()
    if np.all(ang_vel == np.zeros(3)):
        ang_vel = np.zeros(3)
    else:
        ang_vel = sat1.angular_velocity() / np.linalg.norm(sat1.angular_velocity())
        ang_vel[np.isclose(ang_vel, np.zeros(3))] = 0
    # scale for plotting
    ang_vel = ang_vel * 2e7

    # print("plotted attitude:", euler, " at position: ", pos, " pointing v: ", vector / 2e6)

    m = sat1._attitude_model._earth_magnetic_dipole_moment() * 6e-16

    # get new Earth B vector
    m_earth = sat1._attitude_model._earth_magnetic_dipole_moment()
    actor_position = np.array(sat1.get_position(sat1.local_time))
    actor_velocity = np.array(sat1.get_position_velocity(sat1.local_time)[1])
    r = np.linalg.norm(actor_position)
    r_hat = actor_position / r

    B = 1e-7 * (3 * np.dot(m_earth, r_hat) * r_hat - m_earth) / (r**3)

    B = B * 2e14
    # plot vectors
    # ax.quiver(pos[0], pos[1], pos[2], ang_vel[0], ang_vel[1], ang_vel[2], color="m")
    ax.quiver(pos[0], pos[1], pos[2], vector[0], vector[1], vector[2], linewidths=3, color="r")
    ax.quiver(pos[0], pos[1], pos[2], vector2[0], vector2[1], vector2[2], linewidths=3, color="m")
    if not i % 10:
        ax.quiver(0, 0, 0, m[0], m[1], m[2], color="y")
    ax.quiver(pos[0], pos[1], pos[2], B[0], B[1], B[2], color="y")

    sim.advance_time(1000, 0)

# 3D figure limits
axmin = min([min(x), min(y), min(z)]) * 1.1
axmax = max([max(x), max(y), max(z)]) * 1.1

ax.axes.set_xlim3d(left=axmin, right=axmax)
ax.axes.set_ylim3d(bottom=axmin, top=axmax)
ax.axes.set_zlim3d(bottom=axmin, top=axmax)

ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_zlabel("z")

ax.plot(x, y, z)
ax.scatter(0, 0, 0)
plt.show()
