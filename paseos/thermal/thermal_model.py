import numpy as np


class ThermalModel:
    """This model describes the thermal evolution of a spacecraft actor. For the moment, it is a linearized version
    of the single node model from "Spacecraft Thermal Control" by Prof. Isidoro Martínez
    available at http://imartinez.etsiae.upm.es/~isidoro/tc3/Spacecraft%20Thermal%20Modelling%20and%20Testing.pdf

    As simplifications, we assume spacecraft to be spherical black-bodies
    """

    # Spacecraft parameters
    _actor_sun_absorptance = None
    _actor_infrared_absorptance = None
    _actor_sun_facing_area = None
    _actor_central_body_facing_area = None
    _actor_temperature = None
    _actor_mass = None
    _actor_thermal_capacity = None  # in J / (kg * K)

    # Central body parameters
    _body_reflectance = None
    _body_solar_irradiance = None
    _body_radius = None
    _body_emissivity = None
    _body_surface_temperature = None

    _bolzmann_constant = 5.670374419e-8  # in W m^-2 K^-4

    def __init__(self) -> None:
        pass

    def _initialize_constant_vars(self):
        """This function initializes a bunch of values which will remain constant over actor operations."""
        self._C_solar_input = (
            self._actor_sun_absorptance
            * self._actor_sun_facing_area
            * self._body_solar_irradiance
        )

        self._C_albedo_input = (
            self._actor_sun_absorptance
            * self._actor_central_body_facing_area
            * self._body_reflectance
            * self._body_solar_irradiance
        )

    def _compute_phi(self) -> float:
        pass

    def _compute_solar_input(self):
        # Computes solar input
        # _C_solar_input = _actor_sun_absorptance * _actor_sun_facing_area * _body_solar_irradiance
        # and
        # _C_solar_input * view_factor
        # View factor describes the area facing the sun.
        return self._constant_term_solar_input * (1 + np.cos(self._compute_phi())) / 2

    def _compute_albedo_input(self):
        # Compute albedo input as
        # _C_albedo_input = self._actor_sun_absorptance * self._actor_central_body_facing_area *
        # * self._body_reflectance * self._body_solar_irradiance
        # _C_albedo_input * view_factor_actor_to_planet * view_factor_albedo
        pass

    def _compute_central_body_IR_emission(self):
        pass

    def _compute_actor_emission(self):
        pass

    def update_temperature(self):
        pass

    @property
    def temperature(self) -> float:
        return self._actor_temperature
