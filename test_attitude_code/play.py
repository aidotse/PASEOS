# We use pykep for orbit determination
import pykep as pk
import matplotlib.pyplot as plt
import numpy as np


import paseos
from paseos.actors.spacecraft_actor import SpacecraftActor
from paseos.actors.actor_builder import ActorBuilder
from paseos.attitude.reference_frame_transfer import body_to_rpy, rpy_to_eci

# Define central body
earth = pk.planet.jpl_lp("earth")

sat1 = ActorBuilder.get_actor_scaffold("sat1", SpacecraftActor, pk.epoch(0))

ActorBuilder.set_orbit(
    sat1,
    position=[10000000, 1e-3, 1e-3],
    velocity=[1e-3, 8000, 1e-3],
    epoch=pk.epoch(0),
    central_body=earth,
)

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

ActorBuilder.set_attitude_model(sat1)

ActorBuilder.set_disturbances(sat1,True, True)

"""
att_list = []
for i in range(0,10):
    att_list.append(sat1.attitude_in_deg()[0])
    sat1._attitude_model.update_attitude(0.1)
plt.plot(range(0,10), att_list)
plt.show()
"""
"""
x = []
y = []
z = []
for i in range(100):
    x.append()

"""
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
"""
for i in range(100):
    sim.advance_time(440,0)
    x.append(sat1.get_position(sat1.local_time)[0])
    y.append(sat1.get_position(sat1.local_time)[1])
    z.append(sat1.get_position(sat1.local_time)[2])
    print(sat1.attitude_in_deg(), i)
"""
ax = plt.figure().add_subplot(111, projection='3d')
for i in range(20):
    sim.advance_time(100,0)

    pos = (sat1.get_position(sat1.local_time))
    x.append(sat1.get_position(sat1.local_time)[0])
    y.append(sat1.get_position(sat1.local_time)[1])
    z.append(sat1.get_position(sat1.local_time)[2])

    euler = sat1.attitude_in_rad()
    """
    pointing_vector.append(
        rpy_to_eci(body_to_rpy([0,0,1], pointing_vector_in_body),
                   sat1.get_position_velocity(sat1.local_time)[0],
                   sat1.get_position_velocity(sat1.local_time)[1]))
    """
    vector = rpy_to_eci(body_to_rpy([0,0,1], euler),
                   sat1.get_position_velocity(sat1.local_time)[0],
                   sat1.get_position_velocity(sat1.local_time)[1])
    print(pos, sat1.attitude_in_deg())
    ax.quiver(pos[0], pos[1], pos[2], vector[0], vector[1], vector[2], length=0.2)
axmin = min(pos)
axmax = max(pos)
ax.axes.set_xlim3d(left=axmin, right=axmax)
ax.axes.set_ylim3d(bottom=axmin, top=axmax)
ax.axes.set_zlim3d(bottom=axmin, top=axmax)
ax.plot(x,y,z)
ax.scatter(0,0,0)
plt.show()
#%%
# Write an animation of the next 50 steps a 100s to a file called test.mp4
# plotter.animate(sim,dt=200,steps=100,save_to_file="test")

