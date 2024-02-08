import pykep as pk
import os
import numpy as np
from skyfield.api import load
from .sky_field_sky_coordinate import SkyfieldSkyCoordinate
from ..actors.spacecraft_actor import SpacecraftActor
from ..actors.ground_station_actor import GroundstationActor

_SKYFIELD_EARTH_PATH = os.path.join(os.path.dirname(__file__) + "/../resources/", "de421.bsp")
# Skyfield Earth, in the future we may not always want to load this.
_SKYFIELD_EARTH = load(_SKYFIELD_EARTH_PATH)["earth"]


def calc_dist_and_alt_angle_spacecraft_ground(spacecraft_actor, ground_station_actor, epoch: pk.epoch) -> (
        float, float):
    """Calculates distance and elevation angle based on spacecraft and ground station positions.

        Args:
            spacecraft_actor (SpacecraftActor): the spacecraft actor model.
            ground_station_actor (GroundStationActor): the ground station actor model.
            epoch (pk.epoch): the current epoch.

        Returns:
            distance, elevation (float, float): the distance in m and the elevation angle in degrees.
    """
    # Converting time to skyfield to use its API
    t_skyfield = ground_station_actor._skyfield_timescale.tt_jd(epoch.jd)

    # Ground station location in barycentric
    gs_position = (_SKYFIELD_EARTH + ground_station_actor._skyfield_position).at(t_skyfield)

    # Actor position in barycentric
    other_actor_pos = SkyfieldSkyCoordinate(
        r_in_m=np.array(spacecraft_actor.get_position(epoch)),
        earth_pos_in_au=_SKYFIELD_EARTH.at(t_skyfield).position.au,
    )

    # Trigger observation calculation
    observation = gs_position.observe(other_actor_pos).apparent()

    # Compute angle
    altitude_angle = observation.altaz()[0].degrees
    distance = observation.distance().m

    return distance, altitude_angle


def calc_dist_and_alt_angle_spacecraft_spacecraft(local_actor, known_actor, epoch: pk.epoch) -> (float, float):
    """Calculates distance and elevation angle between two spacecraft.

        Args:
            local_actor (SpacecraftActor): the local spacecraft actor model.
            known_actor (SpacecraftActor): the other spacecraft actor model.
            epoch (pk.epoch): the current epoch.

        Returns:
            distance, elevation (float, float): the distance in m and 0 for the elevation angle.
    """

    local_actor_pos = np.array(local_actor.get_position(epoch))
    other_actor_pos = np.array(known_actor.get_position(epoch))

    distance = np.sqrt(
        (local_actor_pos[0] - other_actor_pos[0]) ** 2 + (local_actor_pos[1] - other_actor_pos[1]) ** 2 + (
                local_actor_pos[2] - other_actor_pos[2]) ** 2)
    altitude_angle = 0

    return distance, altitude_angle


def calc_dist_and_alt_angle(local_actor, known_actor, epoch: pk.epoch):
    """Calculates distance and elevation angle between two actors.

        Args:
            local_actor (BaseActor): the local actor model.
            known_actor (BaseActor): the other actor model.
            epoch (pk.epoch): the current epoch.

        Returns:
            distance, elevation (float, float): the distance in m and the elevation angle in degrees.
    """

    if isinstance(local_actor, SpacecraftActor) and isinstance(known_actor, GroundstationActor):
        return calc_dist_and_alt_angle_spacecraft_ground(local_actor, known_actor, epoch)
    elif isinstance(local_actor, SpacecraftActor) and isinstance(known_actor, SpacecraftActor):
        return calc_dist_and_alt_angle_spacecraft_spacecraft(local_actor, known_actor, epoch)
    else:
        print("No suitable types for distance calculations.")
        return None
