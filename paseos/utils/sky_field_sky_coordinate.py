from skyfield.units import AU_M
from skyfield.vectorlib import VectorFunction


class SkyfieldSkyCoordinate(VectorFunction):
    """Small helper class to compute altitude angle"""

    def __init__(self, r_in_m, earth_pos_in_au):
        # Value 0 corresponds to the solar system barycenter according to
        # this: https://rhodesmill.org/skyfield/api-vectors.html#skyfield.vectorlib.VectorFunction.center
        self.center = 0
        # Position vector
        self.r = earth_pos_in_au + r_in_m / AU_M

    @property
    def target(self):
        # This is a property to avoid circular references as described
        # here: https://github.com/skyfielders/python-skyfield/blob/master/skyfield/planetarylib.py#L222
        return self

    def _at(self, t):
        # Velocity vector
        v = [0.0, 0.0, 0.0]
        return self.r, v, self.center, "SkyfieldSkyCoordinate"
