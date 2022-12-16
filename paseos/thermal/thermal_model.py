class ThermalModel:
    """This model describes the thermal evolution of a spacecraft actor. For the moment, it is a linearized version
    of the single node model from "Spacecraft Thermal Control" by Prof. Isidoro Martínez
    available at http://imartinez.etsiae.upm.es/~isidoro/tc3/Spacecraft%20Thermal%20Modelling%20and%20Testing.pdf

    As simplifications, we assume spacecraft to be spherical black-bodies
    """

    _actor = None

    # Spacecraft parameters
    _actor_sun_absorptance = None
    _actor_infrared_absorptance = None
    _actor_sun_facing_area = None
    _actor_central_body_facing_area = None
    _actor_emissive_area = None
    _actor_temperature = None
    _actor_thermal_capacity = None  # in J / (kg * K)

    # Central body parameters
    _body_reflectance = None
    _body_solar_irradiance = None
    _body_radius = None
    _body_emissivity = None
    _body_surface_temperature = None

    _bolzmann_constant = 5.670374419e-8  # in W m^-2 K^-4

    def __init__(self, local_actor) -> None:
        self._actor = local_actor
        self._body_radius = self._actor._central_body.radius

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

        self._C_body_emission = (
            self._actor_infrared_absorptance
            * self._body_emissivity
            * self._actor_central_body_facing_area
            * self._bolzmann_constant
            * self._body_surface_temperature**4
        )

        self._C_actor_emission = (
            self._actor_infrared_absorptance
            * self._actor_emissive_area
            * self._bolzmann_constant
        )

    def _compute_body_view_from_actor(self) -> None:
        h = self._actor.altitude / self._body_radius
        return 1.0 / (h * h)

    def _compute_solar_input(self):
        # Computes solar input
        return self._constant_term_solar_input * (1.0 - self._actor.is_in_eclipse())

    def _compute_albedo_input(self):
        # Compute albedo input as
        # TODO consider phi, for now we assume constant albedo if not in eclipse
        return self._C_albedo_input * 0.5 * (1.0 - self._actor.is_in_eclipse())

    def _compute_central_body_IR_emission(self):
        # Compute IR emissions of the central body as absorpted by the actor
        return self._C_body_emission * self._compute_body_view_from_actor()

    def _compute_actor_emission(self):
        # Compute amount of IR emitted by the spacecraft to space
        return self._C_actor_emission * self._actor_temperature**4

    def update_temperature(self, dt: float):
        total_change_in_W = (
            self._compute_solar_input()
            + self._compute_albedo_input()
            + self._compute_central_body_IR_emission()
            + self._compute_actor_emission()
        )
        self._actor_temperature = self._actor_temperature + ...
        (dt * total_change_in_W) / (self._actor.mass * self._actor_thermal_capacity)

    @property
    def temperature(self) -> float:
        return self._actor_temperature
