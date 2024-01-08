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


def eci_to_rpy(u, r, v, translation=False):
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


def rpy_to_eci(u, r, v, translation=False):
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
        return np.array(u)
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
        return np.array(u)
    else:
        T = np.linalg.inv(transformation_matrix_rpy_body(euler_angles_in_rad))
        return T @ np.array(u)

# next two functions don't work
def angle_between_vectors(u, v, n):
    """Returns right-handed rotation angle between  u and v, with u being the reference for measuring the right-handed
    rotation. Formula:
                        angle = arctan2( u x v . n, u . v)

    Args:
        u (numpy ndarray): reference vector
        v (numpy ndarray): rotated vector
        n (numpy ndarray): plane normal vector

    Returns: float angle in radians

    """
    # todo: solve problem when two
    return np.arctan2(np.linalg.multi_dot([np.cross(u, v), n]), np.linalg.multi_dot([u, v]))

# getting euler angls from one vector is impossible
def get_euler(u, v):
#def get_euler(u):
    """Returns euler angles between two vectors in the same reference frame

    Args:
        u (numpy ndarray): vector 1
        v (numpy ndarray): vector 2

    Returns: numpy ndarray ([roll, pitch, yaw]) in radians
    """
    """
    # roll: angle between yz components
    # normal vector = x-axis
    u_yz = np.array([0, u[1], u[2]])
    v_yz = np.array([0, v[1], v[2]])
    roll = angle_between_vectors(u_yz, v_yz, np.array([1,0,0]))

    # pitch: angle between xz components
    # normal vector = y-axis
    u_xz = np.array([u[0], 0, u[2]])
    v_xz = np.array([v[0], 0, v[2]])
    pitch = angle_between_vectors(u_xz, v_xz, np.array([0,1,0]))

    # yaw: angle between xy components
    # normal vector = z-axis
    u_xy = np.array([u[0], u[1], 0])
    v_xy = np.array([v[0], v[1], 0])
    yaw = angle_between_vectors(u_xy, v_xy, np.array([0,0,1]))
    """

    roll = angle_between_vectors(u, v, np.array([1, 0, 0]))
    pitch = angle_between_vectors(u, v, np.array([0,1,0]))
    yaw = angle_between_vectors(u, v, np.array([0,0,1]))
    """
    # just vector u wrt rpy frame.
    roll =  angle_between_vectors(u, np.array([0, 0, 1]), np.array([1, 0, 0]))
    pitch = angle_between_vectors(u, np.array([0, 0, 1]), np.array([0, 1, 0]))
    yaw =   angle_between_vectors(u, np.array([0, 0, 1]), np.array([0, 0, 1]))
    """
    return [roll, pitch, yaw]

def rodriguez_rotation(p, angles):
    """Rotates vector p around the rotation vector v in the same reference frame.
    
    Args:
        p (numpy ndarray): vector to be rotated [x, y, z]
        angles (numpy ndarray): vector with decomposed rotation angles [theta_x, theta_y, theta_z]

    Returns:
        numpy ndarray, new vector p rotated with given angles

    """
    # scalar rotation:
    theta = np.linalg.norm(angles)
    
    # no rotation: 
    if theta == 0.0:
        return p
    # non-zero rotation
    else:
        # unit rotation vector
        k = angles / theta

        # Rodriguez' formula:
        p_rotated = ((p * np.cos(theta) +
                      (np.cross(k, p)) * np.sin(theta)) +
                     k * (np.linalg.multi_dot([k, p])) *(1 - np.cos(theta)))
        return p_rotated

def rpy_to_body_two(u, rpy_angles):
    # same as rpy_to_body but just a test
    x = np.array([rpy_angles[0], 0, 0])
    y = np.array([0, rpy_angles[1], 0])
    z = np.array([0, 0, rpy_angles[2]])

    # yaw: rotation around z-axis
    u = rodriguez_rotation(u, z)
    y = rodriguez_rotation(y, z)
    x = rodriguez_rotation(x, z)

    # pitch: rotation about new y-axis
    u = rodriguez_rotation(u, y)
    x = rodriguez_rotation(x, y)

    # roll: rotation about new x-axis
    u = rodriguez_rotation(u, x)

    return u

#todo: gives negative angles
def get_rpy_angles(x, y, z, vectors_in_rpy_frame = True):
    """Returns Roll, Pitch, Yaw angles of rotated frame wrt fixed frame.
    example: input body frame primary axes expressed wrt rpy frame, returns roll, pitch, yaw of body
    
    Args:
        x (numpy ndarray): new orientation of [1,0,0] vector expressed in fixed reference frame
        y (numpy ndarray): new orientation of [0,1,0] vector expressed in fixed reference frame
        z (numpy ndarray): new orientation of [0,0,1] vector expressed in fixed reference frame
        vectors_in_rpy_frame (boolean): are the input vectors expressed in the rpy frame? (default: True)

    Returns: list of floats [roll, pitch, yaw]

    """                           # | R00   R01   R02 |
    # create rotation matrix:   R = | R10   R11   R12 |
                                  # | R20   R21   R22 |
    R = np.c_[x, y, z]
    if vectors_in_rpy_frame:
        # different transformation matrix
        R = np.linalg.inv(R)
    # when pitch = +- 90 degrees(R_03 = +-1), yaw and roll have the same effect. Choose roll to be zero
    if np.isclose(R[0][2], -1):
        pitch = np.pi/2
        roll = 0.0
        yaw = -np.arctan2(R[1][0], R[2][0])
        # or yaw = -np.arctan2( - R[2][1], R[1][1])
    elif np.isclose(R[0][2], 1):
        pitch = - np.pi/2
        roll = 0.0
        yaw = np.arctan2( - R[1][0], R[2][0])
        # or yaw = np.arctan2( - R[2][1], - R[1][1])
    else:
        # problem: two rpy sets possible as pitch = atan2( ..., +- sqrt(..)). Positive x component of atan2 is chosen
        pitch = np.arctan2(-R[0][2], np.sqrt((R[1][2]) ** 2 + (R[2][2]) ** 2))
        roll = np.arctan2(R[1][2] / np.cos(pitch), R[2][2] / np.cos(pitch))
        yaw = np.arctan2(R[0][1] / np.cos(pitch), R[0][0] / np.cos(pitch))

    return [roll, pitch, yaw]


def rotate_body_vectors(x, y, z, p, angle):
    x = rodriguez_rotation(x, angle)
    y = rodriguez_rotation(y, angle)
    z = rodriguez_rotation(z, angle)
    p = rodriguez_rotation(p, angle)
    return x, y, z, p
