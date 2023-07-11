from org.orekit.orbits import KeplerianOrbit, PositionAngle
from org.orekit.time import AbsoluteDate
from org.orekit.utils import Constants
from org.orekit.frames import FramesFactory
from org.orekit.orbits import OrbitType
from org.orekit.propagation.numerical import NumericalPropagator
from org.hipparchus.ode.nonstiff import DormandPrince853Integrator
from org.orekit.propagation import SpacecraftState
from org.orekit.utils import IERSConventions
from org.orekit.forces.gravity.potential import GravityFieldFactory
from org.orekit.forces.gravity import HolmesFeatherstoneAttractionModel

from orekit import JArray_double


class OrekitPropagator:
    """This class serves as a wrapper to orekit. It initializes the orekit
    virtual machine and provides a method to propagate a satellite orbit.

    It follows the example from the orekit documentation:

    https://gitlab.orekit.org/orekit-labs/python-wrapper/-/blob/master/examples/Propagation.ipynb
    """

    # Some Constants
    minStep = 0.0001
    maxstep = 1000.0
    initStep = 60.0
    positionTolerance = 1.0

    def __init__(self, orbital_elements: list, epoch: AbsoluteDate, satellite_mass: float) -> None:
        """Initialize the propagator.

        Args:
            orbital_elements (list): List of orbital elements.
            epoch (AbsoluteDate): Epoch of the orbit.
            satellite_mass (float): Mass of the satellite.
        """

        # Inertial frame where the satellite is defined
        inertialFrame = FramesFactory.getEME2000()

        # Unpack the orbital elements
        a, e, i, omega, raan, lv = orbital_elements

        self.initialDate = epoch

        # Orbit construction as Keplerian
        initialOrbit = KeplerianOrbit(
            a,
            e,
            i,
            omega,
            raan,
            lv,
            PositionAngle.TRUE,
            inertialFrame,
            epoch,
            Constants.WGS84_EARTH_MU,
        )

        # Set up the numerical propagator tolerance
        tolerances = NumericalPropagator.tolerances(
            self.positionTolerance, initialOrbit, initialOrbit.getType()
        )

        # Set up the numerical integrator
        integrator = DormandPrince853Integrator(
            self.minStep,
            self.maxstep,
            JArray_double.cast_(
                tolerances[0]
            ),  # Double array of doubles needs to be casted in Python
            JArray_double.cast_(tolerances[1]),
        )
        integrator.setInitialStepSize(self.initStep)

        # Define the initial state of the spacecraft
        satellite_mass = 100.0  # The models need a spacecraft mass, unit kg.
        initialState = SpacecraftState(initialOrbit, satellite_mass)

        # Set up the numerical propagator
        self.propagator_num = NumericalPropagator(integrator)
        self.propagator_num.setOrbitType(OrbitType.CARTESIAN)
        self.propagator_num.setInitialState(initialState)

        # Add the force models
        gravityProvider = GravityFieldFactory.getNormalizedProvider(10, 10)
        self.propagator_num.addForceModel(
            HolmesFeatherstoneAttractionModel(
                FramesFactory.getITRF(IERSConventions.IERS_2010, True), gravityProvider
            )
        )

    def eph(self, time_since_epoch_in_seconds: float):
        """Get the position and velocity of the satellite at a given time since epoch.

        Args:
            time_since_epoch_in_seconds (float): Time since epoch in seconds.

        Returns:
            orekit SpacecraftState: The position and velocity of the satellite.
        """
        state = self.propagator_num.propagate(
            self.initialDate, self.initialDate.shiftedBy(time_since_epoch_in_seconds)
        )

        return state
