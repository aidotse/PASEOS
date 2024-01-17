import math
import pykep as pk
import os
import numpy as np
from skyfield.units import AU_M
from skyfield.api import load
from skyfield.vectorlib import VectorFunction
from .sky_field_sky_coordinate import SkyfieldSkyCoordinate
from ..actors.spacecraft_actor import SpacecraftActor
from ..actors.ground_station_actor import GroundstationActor

_SKYFIELD_EARTH_PATH = os.path.join(os.path.dirname(__file__) + "/../resources/", "de421.bsp")
# Skyfield Earth, in the future we may not always want to load this.
_SKYFIELD_EARTH = load(_SKYFIELD_EARTH_PATH)["earth"]

def calc_radio_gain_from_wavelength_diameter(wavelength, antenna_diameter, antenna_efficiency):
    """Calculates antenna gain (directivity) based on wavelength and diameter, valid for parabolic antennas.

        Args:
            wavelength (float): The wavelength of the signal, in meters.
            antenna_diameter (int): The diameter of the antenna, in meters.

        Returns:
            The antenna gain (directivity) in dB
        """
    assert wavelength > 0, "Wavelength needs to be larger than 0."
    assert antenna_diameter > 0, "Antenna diameter needs to be larger than 0."
    assert antenna_efficiency > 0 and antenna_efficiency <= 1, "Antenna efficiency should be between 0 and 1."
    return 10 * math.log10(antenna_efficiency * (math.pi * antenna_diameter / wavelength)**2)

def calc_optical_gain_from_wavelength_diameter(wavelength, antenna_diameter, antenna_efficiency):
    """Calculates antenna gain (directivity) based on wavelength and diameter, valid for parabolic antennas.

        Args:
            wavelength (float): The wavelength of the signal, in meters.
            antenna_diameter (int): The diameter of the antenna, in meters.

        Returns:
            The antenna gain (directivity) in dB
        """
    assert wavelength > 0, "Wavelength needs to be larger than 0."
    assert antenna_diameter > 0, "Antenna diameter needs to be larger than 0."
    assert antenna_efficiency > 0 and antenna_efficiency <= 1, "Antenna efficiency should be between 0 and 1."
    antenna_radius = antenna_diameter / 2
    aperture_area = math.pi * antenna_radius ** 2
    return 10 * math.log10(antenna_efficiency * (4 * math.pi * aperture_area / wavelength**2))

def calc_gain_from_fwhm(fwhm):
    assert fwhm > 0, "FWHM needs to be larger than 0."

    result = 10 * math.log10((4 * math.sqrt(math.log(2)) / fwhm)**2)
    return result

def calc_dist_and_alt_angle_spacecraft_ground(spacecraft_actor, ground_station_actor, epoch: pk.epoch):
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

def calc_dist_and_alt_angle_spacecraft_spacecraft(local_actor, known_actor, epoch:pk.epoch):

    # Timescale object to convert from pykep epoch to skyfield time
    skyfield_timescale = load.timescale()

    # Converting time to skyfield to use its API
    t_skyfield = skyfield_timescale.tt_jd(epoch.jd)

    # Actor position in barycentric
    # local_actor_pos = SkyfieldSkyCoordinate(
    #     r_in_m=np.array(local_actor.get_position(epoch)),
    #     earth_pos_in_au=_SKYFIELD_EARTH.at(t_skyfield).position.au,
    # )

    # other_actor_pos = SkyfieldSkyCoordinate(
    #     r_in_m=np.array(known_actor.get_position(epoch)),
    #     earth_pos_in_au=_SKYFIELD_EARTH.at(t_skyfield).position.au,
    # )

    local_actor_pos = np.array(local_actor.get_position(epoch))
    other_actor_pos = np.array(known_actor.get_position(epoch))

    distance = np.sqrt((local_actor_pos[0] - other_actor_pos[0])**2 + (local_actor_pos[1] - other_actor_pos[1])**2 + (local_actor_pos[2] - other_actor_pos[2])**2)
    altitude_angle = 0

    return distance, altitude_angle

def calc_dist_and_alt_angle(local_actor, known_actor, epoch: pk.epoch):
    
    if (isinstance(local_actor, SpacecraftActor) and isinstance(known_actor, GroundstationActor)):
        return calc_dist_and_alt_angle_spacecraft_ground(local_actor, known_actor, epoch)
    elif(isinstance(local_actor, SpacecraftActor) and isinstance(known_actor, SpacecraftActor)):
        return calc_dist_and_alt_angle_spacecraft_spacecraft(local_actor, known_actor, epoch)
    else:
        print("No suitable types for distance calculations.")
        return None