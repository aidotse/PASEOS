# We use pykep for orbit determination
import pykep as pk

import paseos
from paseos.actors.spacecraft_actor import SpacecraftActor
from paseos.actors.actor_builder import ActorBuilder
paseos.set_log_level("INFO")

# Define central body
earth = pk.planet.jpl_lp("earth")
sat1 = ActorBuilder.get_actor_scaffold(
        "sat1", SpacecraftActor, pk.epoch(0)
    )
sat2 = ActorBuilder.get_actor_scaffold(
    "sat2", SpacecraftActor, pk.epoch(0)
)

# Define local actor
sat3 = ActorBuilder.get_actor_scaffold(
    "sat3", SpacecraftActor, pk.epoch(0)
)
ActorBuilder.set_orbit(sat3, [-10000000, 0.1, 0.1], [0, 8000.0, 0], pk.epoch(0), earth)
ActorBuilder.set_power_devices(sat3, 500, 10000, 1)

sat4 = ActorBuilder.get_actor_scaffold(
    "sat4", SpacecraftActor, pk.epoch(0)
)
ActorBuilder.set_orbit(sat4, [0, 10000000, 0], [0, 0, 8000.0], pk.epoch(0), earth)


ActorBuilder.set_orbit(
    sat1,
    position=[10000000, 1e-3, 1e-3],
    velocity=[1e-3, 8000, 1e-3],
    epoch=pk.epoch(0),
    central_body=earth,
)
ActorBuilder.set_orbit(
    sat2,
    position=[10000000, 1e-3, 1e-3],
    velocity=[1e-3, -8000, 1e-3],
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

# Add communication link
ActorBuilder.add_comm_device(sat1, device_name="link1", bandwidth_in_kbps=1)
ActorBuilder.add_comm_device(sat2, device_name="link1", bandwidth_in_kbps=2)
ActorBuilder.set_power_devices(sat1, 500, 10000, 1)
ActorBuilder.set_power_devices(sat2, 500, 10000, 1)
sim = paseos.init_sim(sat1)
sim.add_known_actor(sat2)
sim.add_known_actor(sat3)
sim.add_known_actor(sat4)

# Plot current status of PASEOS and get a plotter
plotter = paseos.plot(sim, paseos.PlotType.SpacePlot)
#%%
# Run some operations and inbetween update PASEOS
for i in range(100):
    sim.advance_time(10,0)
    plotter.update(sim)
#%%
# Write an animation of the next 50 steps a 100s to a file called test.mp4
plotter.animate(sim,dt=200,steps=100,save_to_file="test")