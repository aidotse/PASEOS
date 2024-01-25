"""this file contains functions that return attitude disturbance torque vectors expressed in the actor body frame"""

# OUTPUT NUMPY ARRAYS
# OUTPUT IN BODY FRAME
import numpy as np


def calculate_aero_torque():
    # calculations for torques
    # T must be in actor body fixed frame (to be discussed)
    T = [0, 0, 0]
    return np.array(T)


def calculate_grav_torque(u_r, u_n, J, h):
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
        h (float): The altitude of the spacecraft in m

    Returns:
        np.array: total gravitational torques in Nm expressed in the spacecraft body frame
    """
    # Constants
    mu = 3.986004418e14  # Earth's gravitational parameter, [m^3/s^2]
    J2 = 1.0826267e-3  # Earth's J2 coefficient, from https://ocw.tudelft.nl/wp-content/uploads/AE2104-Orbital-Mechanics-Slides_8.pdf
    Re = 6371000  # Earth's radius, [m]

    # Simulation parameters
    r = h + Re  # Radial distance from Satellite center of gravity to Earth's center of gravity, [m]

    tg_term_1 = np.cross((3 * mu * u_r / (r ** 3)), J * u_r)
    tg_term_2 = 30 * np.dot(u_r, u_n) * (np.cross(u_n, J * u_r) + np.cross(u_r, J * u_n))
    tg_term_3 = np.cross((15 - 105 * np.dot(u_r, u_n) ** 2 * u_r), J * u_r) + np.cross(6 * u_n, J * u_r)
    tg = tg_term_1 + mu * J2 * Re ** 2 / (2 * r ** 5) * (tg_term_2 + tg_term_3)
    T = [tg[0,0], tg[1,1], tg[2,2]]
    return np.array(T)


def calculate_magnetic_torque():
    # calculations for torques
    # T must be in actor body fixed frame (to be discussed)
    T = [0, 0, 0]
    return np.array(T)
