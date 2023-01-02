from loguru import logger


class ThermalModel:
    """This model describes the thermal evolution of a spacecraft actor.
    For the moment, it is a slightly simplified version
    of the single node model from "Spacecraft Thermal Control" by Prof. Isidoro Martínez
    available at http://imartinez.etsiae.upm.es/~isidoro/tc3/Spacecraft%20Thermal%20Modelling%20and%20Testing.pdf

    As simplifications, we assume spacecraft to be spherical black-bodies.
    """

    _actor = None

    # Spacecraft parameters
    _actor_sun_absorptance = None  # 0 to 1, for solar input
    _actor_infrared_absorptance = None  # 0 to 1, for body IR input
    _actor_sun_facing_area = None  # for solar input
    _actor_central_body_facing_area = None  # for body IR input
    _actor_emissive_area = None  # to compute heat dissipation
    _actor_temperature_in_K = None  # current operating temperature
    _actor_thermal_capacity = None  # in J / (kg * K)

    # Central body parameters
    _body_reflectance = None  # for albedo input
    _body_solar_irradiance = None  # for solar input
    _body_radius = None  # for body IR input
    _body_emissivity = None  # for body IR input
    _body_surface_temperature_in_K = None  # for body IR input

    # Ratio at which activities generate heat
    _power_consumption_to_heat_ratio = None

    _boltzmann_constant = 5.670374419e-8  # in W m^-2 K^-4

    def __init__(
        self,
        local_actor,
        actor_initial_temperature_in_K: float,
        actor_sun_absorptance: float,
        actor_infrared_absorptance: float,
        actor_sun_facing_area: float,
        actor_central_body_facing_area: float,
        actor_emissive_area: float,
        actor_thermal_capacity: float,
        body_solar_irradiance: float = 1360,
        body_surface_temperature_in_K: float = 288**4,
        body_emissivity: float = 0.6,
        body_reflectance: float = 0.3,
        power_consumption_to_heat_ratio: float = 0.5,
    ) -> None:
        logger.trace("Initializing thermal model.")
        self._actor = local_actor
        self._body_radius = self._actor._central_body.radius

        self._power_consumption_to_heat_ratio = power_consumption_to_heat_ratio

        self._actor_temperature_in_K = actor_initial_temperature_in_K
        self._actor_sun_absorptance = actor_sun_absorptance
        self._actor_infrared_absorptance = actor_infrared_absorptance
        self._actor_sun_facing_area = actor_sun_facing_area
        self._actor_central_body_facing_area = actor_central_body_facing_area
        self._actor_emissive_area = actor_emissive_area
        self._actor_thermal_capacity = actor_thermal_capacity

        self._body_emissivity = body_emissivity
        self._body_solar_irradiance = body_solar_irradiance
        self._body_surface_temperature_in_K = body_surface_temperature_in_K
        self._body_reflectance = body_reflectance

        self._initialize_constant_vars()

    def _initialize_constant_vars(self):
        """This function initializes a bunch of values which will remain constant over actor operations."""
        logger.trace("Initializing thermal model constants.")

        self._C_solar_input = (
            self._actor_sun_absorptance
            * self._actor_sun_facing_area
            * self._body_solar_irradiance
        )
        logger.trace(f"self._C_solar_input={self._C_solar_input}")

        self._C_albedo_input = (
            self._actor_sun_absorptance
            * self._actor_central_body_facing_area
            * self._body_reflectance
            * self._body_solar_irradiance
        )
        logger.trace(f"self._C_albedo_input={self._C_albedo_input}")

        self._C_body_emission = (
            self._actor_infrared_absorptance
            * self._body_emissivity
            * self._actor_central_body_facing_area
            * self._boltzmann_constant
            * self._body_surface_temperature_in_K**4
        )
        logger.trace(f"self._C_body_emission={self._C_body_emission}")

        self._C_actor_emission = (
            self._actor_infrared_absorptance
            * self._actor_emissive_area
            * self._boltzmann_constant
        )
        logger.trace(f"self._C_actor_emission={self._C_actor_emission}")

    def _compute_body_view_from_actor(self) -> None:
        h = self._actor.altitude / self._body_radius
        return 1.0 / (h * h)

    def _compute_solar_input(self):
        # Computes solar input
        # TODO in the future we should consider changing altitude here as well
        solar_input = self._C_solar_input * (1.0 - self._actor.is_in_eclipse())

        logger.trace(f"Solar input is {solar_input}W")
        return solar_input

    def _compute_albedo_input(self):
        # Compute albedo input as
        # TODO consider phi, for now we assume constant albedo if not in eclipse
        albedo_input = self._C_albedo_input * 0.5 * (1.0 - self._actor.is_in_eclipse())
        logger.trace(f"Albedo input is {albedo_input}W")
        return albedo_input

    def _compute_central_body_IR_emission(self):
        # Compute IR emissions of the central body as absorpted by the actor
        emission = self._C_body_emission * self._compute_body_view_from_actor()
        logger.trace(f"Central body emission is {emission}W")
        return emission

    def _compute_actor_emission(self):
        # Compute amount of IR emitted by the spacecraft to space
        emission = self._C_actor_emission * self._actor_temperature_in_K**4
        logger.trace(f"Actor emission is {emission}W")
        return emission

    def update_temperature(self, dt: float, current_power_consumption: float = 0):
        logger.debug(
            f"Updating temperature after {dt} seconds with {current_power_consumption}W being consumed."
        )
        total_change_in_W = (
            self._compute_solar_input()
            + self._compute_albedo_input()
            + self._compute_central_body_IR_emission()
            - self._compute_actor_emission()
            + self._power_consumption_to_heat_ratio * current_power_consumption
        )

        logger.debug(f"Actor's old temperature was {self._actor_temperature_in_K}.")
        logger.trace(f"Actor in eclipse: {self._actor.is_in_eclipse()}")
        logger.trace(f"Actor altitude: {self._actor.altitude}")

        self._actor_temperature_in_K = self._actor_temperature_in_K + (
            dt * total_change_in_W
        ) / (self._actor.mass * self._actor_thermal_capacity)

        # Ensure value cannot go below 0
        self._actor_temperature_in_K = max(0.0, self._actor_temperature_in_K)

        logger.debug(f"Actor's new temperature is {self._actor_temperature_in_K}.")

    @property
    def temperature_in_K(self) -> float:
        return self._actor_temperature_in_K
