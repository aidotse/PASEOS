import math


def calc_radio_gain_from_wavelength_diameter(
    wavelength: float, antenna_diameter: float, antenna_efficiency: float
) -> float:
    """Calculates antenna gain (directivity) based on wavelength and diameter, valid for parabolic antennas.

    Args:
        wavelength (float): The wavelength of the signal, in meters.
        antenna_diameter (int): The diameter of the antenna, in meters.
        antenna_efficiency (float): The antenna efficiency

    Returns:
        The antenna gain (directivity) in dB
    """
    assert wavelength > 0, "Wavelength needs to be larger than 0."
    assert antenna_diameter > 0, "Antenna diameter needs to be larger than 0."
    assert 0 < antenna_efficiency <= 1, "Antenna efficiency should be between 0 and 1."
    return 10 * math.log10(
        antenna_efficiency * (math.pi * antenna_diameter / wavelength) ** 2
    )


def calc_optical_gain_from_wavelength_diameter(
    wavelength: float, antenna_diameter: float, antenna_efficiency: float
) -> float:
    """Calculates antenna gain (directivity) based on wavelength and diameter, valid for parabolic antennas.

    Args:
        wavelength (float): The wavelength of the signal, in meters.
        antenna_diameter (float): The diameter of the antenna, in meters.
        antenna_efficiency (float): The antenna efficiency

    Returns:
        The antenna gain (directivity) in dB
    """
    assert wavelength > 0, "Wavelength needs to be larger than 0."
    assert antenna_diameter > 0, "Antenna diameter needs to be larger than 0."
    assert 0 < antenna_efficiency <= 1, "Antenna efficiency should be between 0 and 1."
    antenna_radius = antenna_diameter / 2
    aperture_area = math.pi * antenna_radius**2
    return 10 * math.log10(
        antenna_efficiency * (4 * math.pi * aperture_area / wavelength**2)
    )


def calc_gain_from_fwhm(fwhm: float) -> float:
    """Calculates gain based on full width at half maximum.

    Args:
        fwhm (float): the full width at half maximum, in rad.

    Returns:
        The gain in dB
    """
    assert fwhm > 0, "FWHM needs to be larger than 0."

    result = 10 * math.log10((4 * math.sqrt(math.log(2)) / fwhm) ** 2)
    return result
