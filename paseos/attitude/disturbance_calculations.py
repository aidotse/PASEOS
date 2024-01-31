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


def calculate_grav_torque(central_body, u_r, u_n, J, r):
    """
    Equation for gravity gradient torque with up to J2 effect from:
    https://doi.org/10.1016/j.asr.2018.06.025, chapter 3.3
    This function currently only works for Earth centered orbits

    Args:
        u_r (np.array): Unit vector pointing from Satellite center of gravity to Earth's center of gravity
        u_n (np.array): Unit vector along the Earth's rotation axis, in the spacecraft body frame
        J (np.array): The satellites moment of inertia, in the form of [[Ixx Ixy Ixz]
                                                                        [Iyx Iyy Iyx]
                                                                        [Izx Izy Izz]]
        r (float): The distance from the center of the Earth to the satellite

    Returns:
        np.array: total gravitational torques in Nm expressed in the spacecraft body frame
    """
    # Constants
    mu = central_body.mu_self  # Earth's gravitational parameter, [m^3/s^2]
    J2 = 1.0826267e-3  # Earth's J2 coefficient, from https://ocw.tudelft.nl/wp-content/uploads/AE2104-Orbital-Mechanics-Slides_8.pdf
    Re = central_body.radius  # Earth's radius, [m]


    tg_term_1 = (3 * mu / (r ** 3))*np.cross(u_r, np.dot(J,u_r))
    tg_term_2 = 30 * np.dot(u_r, u_n)*(np.cross(u_n, np.dot(J,u_r)) + np.cross(u_r, np.dot(J,u_n)))
    tg_term_3 = np.cross((15 - 105 * np.dot(u_r, u_n) ** 2) * u_r, np.dot(J,u_r)) + np.cross(6 * u_n, np.dot(J ,u_n))
    tg = tg_term_1 + mu * J2 * Re ** 2 / (2 * r ** 5) * (tg_term_2 + tg_term_3)
    return np.array(tg)


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
        position (tuple or np.ndarray): actor position
        velocity (tuple or np.ndarray): actor velocity (used for frame transformation)
        attitude (np.ndarray): actor velocity (used for frame transformation)

    Returns: Disturbance torque vector T (nd.array) in Nm in the actor body frame
    """
    # convert to np.ndarray
    position = np.array(position)
    velocity = np.array(velocity)

    # actor distance
    r = np.linalg.norm(position)
    # actor unit position vector
    r_hat = position / r

    # magnetic field flux density at actor's position in Earth inertial frame
    B = 1e-7 * (3 * np.dot(m_earth, r_hat) * r_hat - m_earth) / (r**3)

    # transform field vector to body frame
    B = rpy_to_body(eci_to_rpy(B, position, velocity), attitude)

    # disturbance torque:
    T = np.cross(m_sat, B)
    return T
