"""This file contains functions to transform vectors between three reference frames:

- Earth-centered inertial frame (ECI)

- Roll-Pitch-Yaw frame (RPY):   x: along track direction
                                y: -ĥ (angular momentum of the orbit). perpendicular to the orbital plane
                                z: -r̂ (nadir)

- Body fixed frame:     when body is unperturbed, frame coincides with RPY frame. Perturbations result in non-zero roll
                        pitch and yaw angles, rotating the body fixed frame w.r.t the RPY frame.
"""

import numpy as np


def transformation_matrix_eci_rpy(r, v):
    """
    Creates the transformation matrix to transform a vector in the Earth-Centered Inertial Frame (ECI) to the
    Roll-Pitch-Yaw (RPY) reference frame of the spacecraft (variant to Gaussian reference frame, useful for attitude
    disturbance modelling)

    To go from ECI to RPY, this transformation matrix is used
    To go from RPY to ECI, the inverse is used.

    Args:
        r (list of floats): position vector of RPY reference frame wrt ECI frame
        v (list of floats): velocity of the spacecraft in earth reference frame, centered on spacecraft
    Returns:
        T (numpy array): transformation matrix
    """
    # convert list of floats to numpy arrays
    r = np.array(r)
    v = np.array(v)

    # determine y' base by use of the cross product: (V x r)/||(V x r)||
    cross_vr = np.cross(v, r)
    y = cross_vr / np.linalg.norm(cross_vr)
    # determine z' base by use of the nadir pointing vector
    z = -r / np.linalg.norm(r)
    # determine x' base by use of the cross product: (y' x z')/||(y' x z')||
    cross_yz = np.cross(y, z)
    x = cross_yz / np.linalg.norm(cross_yz)

    # Form transformation matrix
    T = np.array([x, y, z])

    return T


def transformation_matrix_rpy_body(euler_angles_in_rad):
    """Creates the transformation matrix to transform a vector in the Roll-Pitch-Yaw (RPY) reference frame to the body
    fixed reference frame of the spacecraft.

    To go from RPY to body fixed, this transformation matrix is used
    To go from body fixed to RPY, the inverse is used.

    Args:
        euler_angles_in_rad (list of floats): [roll, pitch, yaw] in radians

    Returns:
        T (numpy array of floats): transformation matrix
    """
    roll, pitch, yaw = euler_angles_in_rad

    # individual axis rotations:
    A = np.array([
        [1, 0, 0],
        [0, np.cos(roll), np.sin(roll)],
        [0, -np.sin(roll), np.cos(roll)]
    ])

    B = np.array([
        [np.cos(pitch), 0, -np.sin(pitch)],
        [0, 1, 0],
        [np.sin(pitch), 0, np.cos(pitch)]
    ])

    C = np.array([
        [np.cos(yaw), np.sin(yaw), 0],
        [-np.sin(yaw), np.cos(yaw), 0],
        [0, 0, 1]
    ])

    # Transformation matrix:
    T = A @ B @ C

    return T


def eci_to_rpy(u, r, v, translation=True):
    """Converts a vector in the Earth-Centered Inertial Frame (ECI) to the Roll-Pitch-Yaw (RPY) reference frame of the
    spacecraft, using transformation matrix from transformation_matrix_eci_rpy function.

    Args:
        u (list of floats): vector in ECI
        r (list of floats): position vector of RPY reference frame wrt ECI frame
        v (list of floats): velocity of the spacecraft in earth reference frame, centered on spacecraft
        translation (boolean): does the vector need to be translated? (default=True)

    Returns:
        numpy array of floats: vector u w.r.t. RPY frame
    """

    T = transformation_matrix_eci_rpy(r, v)

    if translation:
        shift = r
    else:
        shift = 0

    # transform u vector with matrix multiplication
    return T@np.array(u) - shift


def rpy_to_eci(u, r, v, translation=True):
    """Converts a vector in the Roll-Pitch-Yaw (RPY) of the spacecraft to the Earth-Centered Inertial Frame (ECI)
    reference frame, using the inverse transformation matrix from transformation_matrix_eci_rpy function.

    Args:
        u (list of floats): vector in RPY
        r (list of floats): position vector of RPY reference frame wrt ECI frame
        v (list of floats): velocity of the spacecraft in earth reference frame, centered on spacecraft
        translation (boolean): does the vector need to be translated? (default=True)

    Returns:
        numpy array of floats: vector u w.r.t. ECI frame
    """

    T = np.linalg.inv(transformation_matrix_eci_rpy(r, v))
    if translation:
        shift = r
    else:
        shift = 0
    # transform u vector with matrix multiplication
    return T@np.array(u) + shift


def rpy_to_body(u, euler_angles_in_rad):
    """Converts a vector in the Roll-Pitch-Yaw (RPY) reference frame to the body fixed reference frame of the
    spacecraft, using transformation matrix from transformation_matrix_rpy_body function.

    Args:
        u (list of floats): vector in RPY
        euler_angles_in_rad (list of floats): [roll, pitch, yaw] in radians

    Returns:
        numpy array of floats: vector u w.r.t. the body fixed frame
    """
    # for undisturbed calculations: zero euler angles result in no transformation
    # numpy default absolute tolerance: 1e-0.8
    if all(np.isclose(euler_angles_in_rad, np.zeros(3))):
        return u
    else:
        T = transformation_matrix_rpy_body(euler_angles_in_rad)
        return T@np.array(u)


def body_to_rpy(u, euler_angles_in_rad):
    """Converts a vector in the body fixed reference frame to the Roll-Pitch-Yaw (RPY) reference frame of the
    spacecraft, using the inverse transformation matrix from transformation_matrix_rpy_body function.

    Args:
        u (list of floats): vector in the body fixed frame
        euler_angles_in_rad (list of floats): [roll, pitch, yaw] in radians

    Returns:
        vector u w.r.t. the RPY frame
    """
    # for undisturbed calculations: zero euler angles result in no transformation
    # numpy default absolute tolerance: 1e-0.8
    if all(np.isclose(euler_angles_in_rad, np.zeros(3))):
        return u
    else:
        T = np.linalg.inv(transformation_matrix_rpy_body(euler_angles_in_rad))
        return T @ np.array(u)
