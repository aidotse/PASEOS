import sys

sys.path.append("../..")

import numpy as np
from paseos.utils.set_log_level import set_log_level
from paseos.utils.load_default_cfg import load_default_cfg
import paseos
from paseos.visualization.space_animation import SpaceAnimation
from paseos.actors.spacecraft_actor import SpacecraftActor
from paseos.actors.actor_builder import ActorBuilder
import pykep as pk

set_log_level("INFO")

# Define central body
earth = pk.planet.jpl_lp("earth")
# Define today (27-10-22)
today = pk.epoch(8335.5, "mjd2000")


S2A = ActorBuilder.get_actor_scaffold("Satellite-A", SpacecraftActor, today)

# Define local actor
S2B = ActorBuilder.get_actor_scaffold("Satellite-B", SpacecraftActor, today)

sentinel2A_line1 = (
    "1 40697U 15028A   22300.01175178 -.00001065  00000+0 -38995-3 0  9999"
)
sentinel2A_line2 = (
    "2 40697  98.5650  12.8880 0001080  78.8662 281.2690 14.30806819383668"
)
sentinel2A = pk.planet.tle(sentinel2A_line1, sentinel2A_line2)

# Calculating S2A ephemerides.
sentinel2A_eph = sentinel2A.eph(today)

sentinel2B_line1 = (
    "1 42063U 17013A   22300.18652110  .00000099  00000+0  54271-4 0  9998"
)
sentinel2B_line2 = (
    "2 42063  98.5693  13.0364 0001083 104.3232 255.8080 14.30819357294601"
)
sentinel2B = pk.planet.tle(sentinel2B_line1, sentinel2B_line2)

# Calculating S2B ephemerides.
sentinel2B_eph = sentinel2B.eph(today)

# Define local actor
S2B = ActorBuilder.get_actor_scaffold("Satellite-B", SpacecraftActor, today)


# Adding orbits around Earth based on previously calculated ephemerides
ActorBuilder.set_orbit(S2A, sentinel2A_eph[0], sentinel2A_eph[1], today, earth)

# To enable the communication between S2A and S2B, the velocity vector is multiplied by - 1 making the satellite to orbit with opposite direction.
ActorBuilder.set_orbit(
    S2B,
    sentinel2B_eph[0],
    [-sentinel2B_eph[1][0], -sentinel2B_eph[1][1], -sentinel2B_eph[1][2]],
    today,
    earth,
)

# Adding power devices
ActorBuilder.set_power_devices(S2A, 500, 10000, 1)
ActorBuilder.set_power_devices(S2B, 500, 10000, 1)
# Adding communication devices.
ActorBuilder.add_comm_device(S2A, "isl_transmitter", 10000)
ActorBuilder.add_comm_device(S2B, "isl_transmitter", 10000)


# init simulation
cfg = load_default_cfg()
cfg.sim.start_time = today.mjd2000 * pk.DAY2SEC
sim = paseos.init_sim(S2A, cfg)
sim.add_known_actor(S2B)


anim = SpaceAnimation(sim)
import matplotlib.pyplot as plt

dt = 100
for t in range(10):
    anim.animate(sim, dt)
    plt.pause(0.05)
plt.show()
