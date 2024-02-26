import os
from skyfield.api import load

BOLTZMANN_DB = -228.6  # in dB
C = 299792458  # in m/s
PLANCK_CONSTANT = 6.62607015e-34  # in m^2 kg / s

REQUIRED_BER_RADIO = 10e-5
REQUIRED_S_N_RATIO_RADIO_DB = 9.6  # in dB
REQUIRED_S_N_MARGIN_RADIO_DB = 4.3  # in dB


WAVELENGTH_OPTICAL = 1550e-9  # in m
REQUIRED_BER_OPTICAL = 10e-3
REQUIRED_S_N_MARGIN_OPTICAL_DB = 3  # in dB
PHOTONS_PER_BIT = 250


_SKYFIELD_EARTH_PATH = os.path.join(os.path.dirname(__file__) + "/../resources/", "de421.bsp")
# Skyfield Earth, in the future we may not always want to load this.
SKYFIELD_EARTH = load(_SKYFIELD_EARTH_PATH)["earth"]
