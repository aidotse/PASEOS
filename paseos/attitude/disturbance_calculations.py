"""this file contains functions that return attitude disturbance torque vectors expressed in the actor body frame"""

# OUTPUT NUMPY ARRAYS
# OUTPUT IN BODY FRAME
import numpy as np


def calculate_aero_torque():
    # calculations for torques
    # T must be in actor body fixed frame (to be discussed)
    T = [0, 0, 0]
    return np.array(T)


def calculate_grav_torque(u_r, u_n, J, r):
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
        h (float): The distance from the center of the Earth to the satellite

    Returns:
        np.array: total gravitational torques in Nm expressed in the spacecraft body frame
    """
    # Constants
    mu = 3.986004418e14  # Earth's gravitational parameter, [m^3/s^2]
    J2 = 1.0826267e-3  # Earth's J2 coefficient, from https://ocw.tudelft.nl/wp-content/uploads/AE2104-Orbital-Mechanics-Slides_8.pdf
    Re = 6371000  # Earth's radius, [m]


    tg_term_1 = (3 * mu / (r ** 3))*np.cross(u_r, np.dot(J,u_r))
    tg_term_2 = 30 * np.dot(u_r, u_n)*(np.cross(u_n, np.dot(J,u_r)) + np.cross(u_r, np.dot(J,u_n)))
    tg_term_3 = np.cross((15 - 105 * np.dot(u_r, u_n) ** 2) * u_r, np.dot(J,u_r)) + np.cross(6 * u_n, np.dot(J ,u_n))
    tg = tg_term_1 + mu * J2 * Re ** 2 / (2 * r ** 5) * (tg_term_2 + tg_term_3)
    return np.array(tg)


def calculate_magnetic_torque():
    # calculations for torques
    # T must be in actor body fixed frame (to be discussed)
    T = [0, 0, 0]
    return np.array(T)
