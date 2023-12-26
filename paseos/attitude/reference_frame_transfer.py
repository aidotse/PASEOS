import numpy as np

def eci_to_rpy(u, r, v):
    """
    Converts a vector in the Earth-Centered Inertial Frame (ECI) to the Roll-Pitch-Yaw (RPY) reference frame of the
    spacecraft (variant to Gaussian reference frame, useful for attitude disturbance modelling)
    x: along track direction
    y: -ĥ (angular momentum of the orbit). perpendicular to the orbital plane
    z: -r̂ (nadir)
    Args:
        u: vector in ECI
        r: position vector of RPY reference frame wrt ECI frame
        v: velocity of the spacecraft in earth reference frame, centered on spacecraft

    Returns:
        vector u w.r.t. RPY frame
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

    # transform u vector with matrix multiplication
    return T@u
