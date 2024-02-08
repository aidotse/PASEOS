"""Test to check the gain_calc function(s)"""
import numpy as np
import pytest

from paseos.utils.gain_calc import (
    calc_radio_gain_from_wavelength_diameter,
    calc_gain_from_fwhm,
)


def test_gain_calculation():
    with pytest.raises(AssertionError, match="Wavelength needs to be larger than 0."):
        calc_radio_gain_from_wavelength_diameter(-5, 0, 0.5)

    with pytest.raises(
        AssertionError, match="Antenna diameter needs to be larger than 0."
    ):
        calc_radio_gain_from_wavelength_diameter(10, -2, 0.5)
    with pytest.raises(
        AssertionError, match="Antenna efficiency should be between 0 and 1."
    ):
        calc_radio_gain_from_wavelength_diameter(10, 2, -0.5)
    with pytest.raises(
        AssertionError, match="Antenna efficiency should be between 0 and 1."
    ):
        calc_radio_gain_from_wavelength_diameter(10, 2, 1.5)

    gain_radio = calc_radio_gain_from_wavelength_diameter(0.035, 15, 0.5)
    assert np.isclose(gain_radio, 59.6, rtol=0.01, atol=1.0)

    gain_optical = calc_gain_from_fwhm(1e-3)
    assert np.isclose(gain_optical, 70.45, rtol=0.01, atol=1)


if __name__ == "__main__":
    test_gain_calculation()
