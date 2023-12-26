import numpy as np

def transformation_matrix_eci_rpy(r, v):
    """
    Creates the transformation matrix  to transform a vector in the Earth-Centered Inertial Frame (ECI) to the
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

def eci_to_rpy(u, r, v):
    """
    Converts a vector in the Earth-Centered Inertial Frame (ECI) to the Roll-Pitch-Yaw (RPY) reference frame of the
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
    """
        Converts a vector in the Roll-Pitch-Yaw (RPY) of the spacecraft to the Earth-Centered Inertial Frame (ECI)
        reference frame, using transformation matrix from transformation_matrix_eci_rpy function.

        Args:
            u: vector in ECI
            r: position vector of RPY reference frame wrt ECI frame
            v: velocity of the spacecraft in earth reference frame, centered on spacecraft

        Returns:
            vector u w.r.t. ECI frame
        """

    T = np.linalg.inv(transformation_matrix_eci_rpy(r, v))

    # transform u vector with matrix multiplication
    return T@u
