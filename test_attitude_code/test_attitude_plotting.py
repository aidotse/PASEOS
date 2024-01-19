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

sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))
sat2 = ActorBuilder.get_actor_scaffold("sat2", SpacecraftActor, pk.epoch(0))

ActorBuilder.set_orbit(
    sat1,
    position=[10000000, 0, 0],
    velocity=[0, 8000, 0],
    epoch=pk.epoch(0),
    central_body=earth,
)
"""
ActorBuilder.set_orbit(
    sat1,
    position=[10000000, 3000000, 0],
    velocity=[0, 8000, 2000],
    epoch=pk.epoch(0),
    central_body=earth,
)
"""
ActorBuilder.set_geometric_model(sat1, mass=500)
print(sat1._moment_of_inertia)

ActorBuilder.set_geometric_model(sat2, mass=5000)
print(sat2._moment_of_inertia)


ActorBuilder.set_thermal_model(
    sat1,
    actor_mass=100,
    actor_initial_temperature_in_K=270,
    actor_sun_absorptance=0.5,
    actor_infrared_absorptance=0.5,
    actor_sun_facing_area=1,
    actor_central_body_facing_area=4,
    actor_emissive_area=18,
    actor_thermal_capacity=0.89,
)
# following used to check if model is correct. Pure rotations around pointing vector should not move the pointing vector.
pure_axis_rotation = [[0.00158, 0.0, 0.0], [0.0, 0.00158, 0.0], [0.0, 0.0, 0.00158]]
axes_list = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
axis = 1    # x:0, y:1, z:2
# when i = 21 in loop, 0.00158 rad/sec will rotate 180 deg about 1 axis
ActorBuilder.set_attitude_model(
    sat1,
    #actor_initial_angular_velocity=pure_axis_rotation[1],
    #actor_pointing_vector_body=axes_list[0],
    actor_initial_angular_velocity=[0.0, 0.00158, 0.0],
    actor_pointing_vector_body=[0.0, 0.0, 1.0],
    actor_initial_attitude_in_rad=[0.0, 0.0, 0.0]
)
ActorBuilder.set_disturbances(sat1,True, True)

sim = paseos.init_sim(sat1)
plt.close()
# Plot current status of PASEOS and get a plotter
#%%
# Run some operations and inbetween update PASEOS
pos = []
x = []
y = []
z = []
pointing_vector = []
ratio = 100/440


fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
for i in range(21):

    pos = sat1.get_position(sat1.local_time)
    x.append(sat1.get_position(sat1.local_time)[0])
    y.append(sat1.get_position(sat1.local_time)[1])
    z.append(sat1.get_position(sat1.local_time)[2])

    euler = sat1.attitude_in_rad()

    # pointing vector:
    vector = sat1.pointing_vector()
    vector[np.isclose(vector, np.zeros(3))] = 0
    vector = vector * 2e6

    # angular velocity vector:
    # normalize first:
    ang_vel = sat1.angular_velocity()
    if all(ang_vel == np.zeros(3)):
        ang_vel = np.zeros(3)
    else:
        ang_vel = sat1.angular_velocity() / np.linalg.norm(sat1.angular_velocity())
        ang_vel[np.isclose(ang_vel, np.zeros(3))] = 0

    ang_vel = ang_vel * 2e6

    # print(i, vector / 2e6, sat1.attitude_in_deg(), sat1.angular_velocity() / 2e6)

    ax.quiver(pos[0], pos[1], pos[2], ang_vel[0], ang_vel[1], ang_vel[2], color="m")
    ax.quiver(pos[0], pos[1], pos[2], vector[0], vector[1], vector[2])
    sim.advance_time(100, 0)
axmin = min([min(x), min(y), min(z)])*1.1
axmax = max([max(x), max(y), max(z)])*1.1

ax.axes.set_xlim3d(left=axmin, right=axmax)
ax.axes.set_ylim3d(bottom=axmin, top=axmax)
ax.axes.set_zlim3d(bottom=axmin, top=axmax)

ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_zlabel("z")

ax.plot(x,y,z)
ax.scatter(0,0,0)
