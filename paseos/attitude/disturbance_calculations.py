"""this file contains functions that return attitude disturbance torque vectors expressed in the actor body frame"""

# OUTPUT NUMPY ARRAYS
# OUTPUT IN BODY FRAME
import numpy as np
from ..utils.reference_frame_transfer import rpy_to_body, eci_to_rpy

def calculate_aero_torque():
    # calculations for torques
    # T must be in actor body fixed frame (to be discussed)
    T = [0, 0, 0]
    return np.array(T)


def calculate_grav_torque():
    # calculations for torques
    # T must be in actor body fixed frame (to be discussed)
    T = [0, 0, 0]
    return np.array(T)


def calculate_magnetic_torque(m_earth, m_sat, position, velocity, attitude):
    """Calculates the external disturbance torque acting on the actor due to the magnetic field of the earth.
    a dipole magnetic field flux density is described by the formula: B = μ0/(4πr³) * [3 r_hat(r_hat ⋅ m) − m]
    With μ0 = 4 π 1e-7 H/m (vacuum permeability), r = actor distance from dipole center, r_hat = unit position vector,
    and m the magnetic dipole moment vector of the Earth (magnitude in the year 2000 = 7.79 x 10²² Am²)

    The disturbance torque is then calculated by: T = m_sat x B
    With m_sat the (residual) magnetic dipole moment vector of the actor, magnitude usually between 0.1 - 20 Am² (SMAD)

    https://en.wikipedia.org/wiki/Magnetic_dipole (or Chow, Tai L. (2006). Introduction to electromagnetic theory:
    a modern perspective, used formular on p. 149)

    Args:
        m_earth (np.ndarray): magnetic dipole moment vector of the Earth in Am²
        m_sat (np.ndarray): magnetic dipole moment vector of the actor, magnitude usually between 0.1 - 20 Am²
        position (np.ndarray): actor position
        velocity (np.ndarray): actor velocity (used for frame transformation)
        attitude (np.ndarray): actor velocity (used for frame transformation)

    Returns: Disturbance torque vector T (nd.array) in Nm in the actor body frame
    """
    # actor distance and unit position vector
    r = np.linalg.norm(position)
    r_hat = position / r

    # magnetic field flux density at actor's position in Earth inertial frame
    B = 1e-7 * (3 * np.dot(m_earth, r_hat) * r_hat - m_earth) / (r ** 3)

    # transform field vector to body frame
    B = rpy_to_body(eci_to_rpy(B, position, velocity), attitude)

    # disturbance torque:
    T = np.cross(m_sat, B)

    return T
