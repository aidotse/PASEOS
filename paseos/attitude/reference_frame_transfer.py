import numpy as np

def transformation_matrix_eci_rpy(r, v):
    """
    Creates the transformation matrix to transform a vector in the Earth-Centered Inertial Frame (ECI) to the
    Roll-Pitch-Yaw (RPY) reference frame of the spacecraft (variant to Gaussian reference frame, useful for attitude
    disturbance modelling)

    RPY reference frame:    x: along track direction
                            y: -ĥ (angular momentum of the orbit). perpendicular to the orbital plane
                            z: -r̂ (nadir)

    To go from ECI to RPY, this transformation matrix is used
    To go from RPY to ECI, the inverse is used.

    Args:
        r (numpy array): position vector of RPY reference frame wrt ECI frame
        v (numpy array): velocity of the spacecraft in earth reference frame, centered on spacecraft
    Returns:
        T (numpy array): transformation matrix
    """

    # determine y' base by use of the cross product: (V x r)/||(V x r)||
    cross_vp = np.cross(v, r)
    y = cross_vp / np.linalg.norm(cross_vp)
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

    RPY reference frame:    x: along track direction
                            y: -ĥ (angular momentum of the orbit). perpendicular to the orbital plane
                            z: -r̂ (nadir)

    body fixed frame:       when unperturbed, coincides with RPY frame. Perturbations result in non-zero roll pitch and
                            yaw angles, rotating the body fixed frame.

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

def eci_to_rpy(u, r, v):
    """Converts a vector in the Earth-Centered Inertial Frame (ECI) to the Roll-Pitch-Yaw (RPY) reference frame of the
    spacecraft, using transformation matrix from transformation_matrix_eci_rpy function.

    Args:
        u: vector in ECI
        r: position vector of RPY reference frame wrt ECI frame
        v: velocity of the spacecraft in earth reference frame, centered on spacecraft

    Returns:
        vector u w.r.t. RPY frame
    """

    T = transformation_matrix_eci_rpy(r, v)

    # transform u vector with matrix multiplication
    return T@u

def rpy_to_eci(u, r, v):
    """Converts a vector in the Roll-Pitch-Yaw (RPY) of the spacecraft to the Earth-Centered Inertial Frame (ECI)
    reference frame, using the inverse transformation matrix from transformation_matrix_eci_rpy function.

    Args:
        u: vector in RPY
        r: position vector of RPY reference frame wrt ECI frame
        v: velocity of the spacecraft in earth reference frame, centered on spacecraft

    Returns:
        vector u w.r.t. ECI frame
    """

    T = np.linalg.inv(transformation_matrix_eci_rpy(r, v))

    # transform u vector with matrix multiplication
    return T@u

def rpy_to_body(u, euler_angles_in_rad):
    """Converts a vector in the Roll-Pitch-Yaw (RPY) reference frame to the body fixed reference frame of the
    spacecraft, using transformation matrix from transformation_matrix_rpy_body function.

    Args:
        u (list of floats): vector in RPY
        euler_angles_in_rad (list of floats): [roll, pitch, yaw] in radians

    Returns:
        vector u w.r.t. the body fixed frame
    """
    T = transformation_matrix_rpy_body(euler_angles_in_rad)
    return T@u

def body_to_rpy(u, euler_angles_in_rad):
    """Converts a vector in the body fixed reference frame to the Roll-Pitch-Yaw (RPY) reference frame of the
    spacecraft, using the inverse transformation matrix from transformation_matrix_rpy_body function.

    Args:
        u (list of floats): vector in the body fixed frame
        euler_angles_in_rad (list of floats): [roll, pitch, yaw] in radians

    Returns:
        vector u w.r.t. the RPY frame
    """
    T = np.linalg.inv(transformation_matrix_rpy_body(euler_angles_in_rad))
    return T @ u
