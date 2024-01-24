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

ActorBuilder.set_orbit(
    sat1,
    position=[10000000, 0, 0],
    velocity=[0, 8000, 0],
    epoch=pk.epoch(0),
    central_body=earth,
)
ActorBuilder.set_geometric_model(sat1, mass=500)

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

# when i = 21 in loop and advance time =100, pi/2000 rad/sec will rotate 180 deg about 1 axis
ActorBuilder.set_attitude_model(
    sat1,
    actor_initial_angular_velocity=[0.0, np.pi / 2000, 0.0],
    actor_pointing_vector_body=[0.0, 0.0, 1.0],
    actor_initial_attitude_in_rad=[0.0, 0.0, 0.0],
)
# disturbances:
# ActorBuilder.set_disturbances(sat1,True, True)
ActorBuilder.set_disturbances(sat1)

sim = paseos.init_sim(sat1)
plt.close()

pos = []
x = []
y = []
z = []
pointing_vector = []

fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")
for i in range(21):
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
    vector = vector * 2e6

    # angular velocity vector:
    # normalize first:
    ang_vel = sat1.angular_velocity()
    if all(ang_vel == np.zeros(3)):
        ang_vel = np.zeros(3)
    else:
        ang_vel = sat1.angular_velocity() / np.linalg.norm(sat1.angular_velocity())
        ang_vel[np.isclose(ang_vel, np.zeros(3))] = 0
    # scale for plotting
    ang_vel = ang_vel * 2e6

    print("plotted attitude:", euler, " at position: ", pos, " pointing v: ", vector/2e6)
    # plot vectors
    ax.quiver(pos[0], pos[1], pos[2], ang_vel[0], ang_vel[1], ang_vel[2], color="m")
    ax.quiver(pos[0], pos[1], pos[2], vector[0], vector[1], vector[2])

    # sim.advance_time(100, 0)
    sim.advance_time(100, 0)


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
