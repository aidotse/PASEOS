"""This file contains functions to transform vectors between three reference frames:

- Earth-centered inertial frame (ECI)

- Roll-Pitch-Yaw frame (RPY):   x: along track direction
                                y: -ĥ (angular momentum of the orbit). perpendicular to the orbital plane
                                z: -r̂ (nadir)

- Body fixed frame:     when body is unperturbed, frame coincides with RPY frame. Perturbations result in non-zero roll
                        pitch and yaw angles, rotating the body fixed frame w.r.t the RPY frame.

It also provides functions for rotating vectors around another vector and determining roll, pitch and yaw angles between
two reference frames.

Note: the order of rotation yaw -> pitch -> roll is used for transforming from "space frame (RPY here)" to body frame
"""

import numpy as np


def transformation_matrix_eci_rpy(r, v):
    """
    Creates the transformation matrix to transform a vector in the Earth-Centered Inertial Frame (ECI) to the
    Roll-Pitch-Yaw (RPY) reference frame of the spacecraft (variant to Gaussian reference frame, useful for attitude
    disturbance modelling).

    To go from ECI to RPY, this transformation matrix is used.
    To go from RPY to ECI, the inverse is used.

    Args:
        r (np.ndarray): position vector of RPY reference frame wrt ECI frame
        v (np.ndarray): velocity of the spacecraft in earth reference frame, centered on spacecraft
    Returns:
        T (np.ndarray): transformation matrix
    """

    # y' coincides with -ĥ vector which is perpendicular to the orbital plane. Thus, perpendicular to v and p vectors
    # determine y' base by use of the cross product: (V x r)/||(V x r)||
    cross_vr = np.cross(v, r)
    y = cross_vr / np.linalg.norm(cross_vr)

    # z' coincides with the nadir pointing vector
    # determine z' base by use of the position vector of the RPY frame
    z = -r / np.linalg.norm(r)

    # x' completes the right-handed frame
    # determine x' base by use of the cross product: (y' x z')/||(y' x z')||
    cross_yz = np.cross(y, z)
    x = cross_yz / np.linalg.norm(cross_yz)

    # Form transformation matrix
    T = np.array([x, y, z])

    return T


def transformation_matrix_rpy_body(euler_angles_in_rad):
    """Creates the transformation matrix to transform a vector in the Roll-Pitch-Yaw (RPY) reference frame to the body.
    fixed reference frame of the spacecraft.

    To go from RPY to body fixed, this transformation matrix is used.
    To go from body fixed to RPY, the inverse is used.

    Args:
        euler_angles_in_rad (np.ndarray): [roll, pitch, yaw] in radians.

    Returns:
        T (np.ndarray): transformation matrix.
    """
    roll, pitch, yaw = euler_angles_in_rad

    # individual axis rotations:
    A = np.array(
        [
            [1, 0, 0],
            [0, np.cos(roll), np.sin(roll)],
            [0, -np.sin(roll), np.cos(roll)]
        ]
    )

    B = np.array(
        [
            [np.cos(pitch), 0, -np.sin(pitch)],
            [0, 1, 0],
            [np.sin(pitch), 0, np.cos(pitch)],
        ]
    )

    C = np.array(
        [
            [np.cos(yaw), np.sin(yaw), 0],
            [-np.sin(yaw), np.cos(yaw), 0],
            [0, 0, 1]]
    )

    # Transformation matrix:
    T = A @ B @ C

    return T


def eci_to_rpy(u, r, v, translation=False):
    """Converts a vector in the Earth-Centered Inertial Frame (ECI) to the Roll-Pitch-Yaw (RPY) reference frame of the
    spacecraft, using transformation matrix from transformation_matrix_eci_rpy function.

    Args:
        u (np.ndarray): vector in ECI
        r (np.ndarray): position vector of RPY reference frame wrt ECI frame
        v (np.ndarray): velocity of the spacecraft in earth reference frame, centered on spacecraft
        translation (bool): does the vector need to be translated? (default=False)

    Returns:
        vector u w.r.t. RPY frame
    """

    T = transformation_matrix_eci_rpy(r, v)

    if translation:
        shift = r
    else:
        shift = 0

    # transform u vector with matrix multiplication
    return T @ u - shift


def rpy_to_eci(u, r, v, translation=False):
    """Converts a vector in the Roll-Pitch-Yaw (RPY) of the spacecraft to the Earth-Centered Inertial Frame (ECI)
    reference frame, using the inverse transformation matrix from transformation_matrix_eci_rpy function.

    Args:
        u (np.ndarray): vector in RPY
        r (np.ndarray): position vector of RPY reference frame wrt ECI frame
        v (np.ndarray): velocity of the spacecraft in earth reference frame, centered on spacecraft
        translation (bool): does the vector need to be translated? (default=False)

    Returns:
        vector u w.r.t. ECI frame
    """

    T = np.linalg.inv(transformation_matrix_eci_rpy(r, v))
    if translation:
        shift = r
    else:
        shift = 0
    # transform u vector with matrix multiplication
    return T @ u + shift


def rpy_to_body(u, euler_angles_in_rad):
    """Converts a vector in the Roll-Pitch-Yaw (RPY) reference frame to the body fixed reference frame of the
    spacecraft, using transformation matrix from transformation_matrix_rpy_body function.

    Args:
        u (np.ndarray): vector in RPY
        euler_angles_in_rad (np.ndarray): [roll, pitch, yaw] in radians

    Returns:
        vector u w.r.t. the body fixed frame
    """
    # for undisturbed calculations: zero euler angles result in no transformation
    # numpy default absolute tolerance: 1e-0.8
    if all(np.isclose(euler_angles_in_rad, np.zeros(3))):
        return u
    else:
        T = transformation_matrix_rpy_body(euler_angles_in_rad)
        return T @ u


def body_to_rpy(u, euler_angles_in_rad):
    """Converts a vector in the body fixed reference frame to the Roll-Pitch-Yaw (RPY) reference frame of the
    spacecraft, using the inverse transformation matrix from transformation_matrix_rpy_body function.

    Args:
        u (np.ndarray): vector in the body fixed frame
        euler_angles_in_rad (np.ndarray): [roll, pitch, yaw] in radians

    Returns:
        vector u w.r.t. the RPY frame
    """
    # for undisturbed calculations: zero euler angles result in no transformation
    # numpy default absolute tolerance: 1e-0.8
    if all(np.isclose(euler_angles_in_rad, np.zeros(3))):
        return u
    else:
        T = np.linalg.inv(transformation_matrix_rpy_body(euler_angles_in_rad))
        return T @ u


def rodrigues_rotation(p, angles):
    """Rotates vector p around the rotation vector v in the same reference frame. Using Rodrigues' rotation formula.

    Args:
        p (np.ndarray): vector to be rotated [x, y, z]
        angles (np.ndarray): vector with decomposed rotation angles [theta_x, theta_y, theta_z]

    Returns:
        new vector p rotated with given angles
    """
    # scalar rotation:
    theta = np.linalg.norm(angles)

    # no rotation:
    if theta == 0.0:
        return p
    # non-zero rotation:
    else:
        # unit rotation vector
        k = angles / theta

        # Rodrigues' formula:
        p_rotated = (p * np.cos(theta) + (np.cross(k, p)) * np.sin(theta)) + k * (
            np.linalg.multi_dot([k, p])
        ) * (1 - np.cos(theta))
        return p_rotated


def get_rpy_angles(x, y, z, vectors_in_rpy_frame=True):
    """Returns Roll, Pitch, Yaw angles of rotated frame wrt fixed frame.
    example: input body frame primary axes expressed wrt rpy frame, returns roll, pitch, yaw of body

    This function assumes the following transformation matrix: where c = cos, s = sin, and the angles being:
    roll (r), pitch (p) and yaw (y)

          | R00   R01   R02 |   |      cp cy                cp sy                -sp  | ^ (-1)
      R = | R10   R11   R12 | = | sr sp cy - cr sy      sr sp sy + cr cy        sr cp |
          | R20   R21   R22 |   | cr sp cy + sr sy      cr sp sy - sr cy        sr cp |

    This is the transformation matrix from RPY to body frame, when the body frame is expressed in RPY, to find the
    roll, pitch, yaw angles, this matrix needs to be inverted.

    Args:
        x (np.ndarray): new orientation of [1,0,0] x-axis expressed in fixed reference frame
        y (np.ndarray): new orientation of [0,1,0] y-axis expressed in fixed reference frame
        z (np.ndarray): new orientation of [0,0,1] z-axis expressed in fixed reference frame
        vectors_in_rpy_frame (bool): are the input vectors expressed in the rpy frame? (default: True)

    Returns:
        roll, pitch, yaw angles
    """
    # transformation matrix:
    R = np.c_[x, y, z]

    if vectors_in_rpy_frame:
        # different transformation matrix
        R = np.linalg.inv(R)

    # when pitch = +- 90 degrees(R_03 = +-1), yaw and roll have the same effect. Choose roll to be zero
    # (avoid dividing by zero)
    if R[0][2] == -1.0:
        pitch = np.pi / 2
        roll = 0.0
        yaw = -np.arctan2(R[1][0], R[2][0])
        # or yaw = -np.arctan2( - R[2][1], R[1][1])
    elif R[0][2] == 1.0:
        pitch = -np.pi / 2
        roll = 0.0
        yaw = np.arctan2(-R[1][0], R[2][0])
        # or yaw = np.arctan2( - R[2][1], - R[1][1])
    else:
        # problem: two rpy sets possible as pitch = atan2( ..., +- sqrt(..)). Positive x component of atan2 is chosen
        pitch = np.arctan2(-R[0][2], np.sqrt((R[1][2]) ** 2 + (R[2][2]) ** 2))
        roll = np.arctan2(R[1][2] / np.cos(pitch), R[2][2] / np.cos(pitch))
        yaw = np.arctan2(R[0][1] / np.cos(pitch), R[0][0] / np.cos(pitch))

    return np.array([roll, pitch, yaw])


def rotate_body_vectors(x, y, z, p, angle):
    """Used for rotating multiple vectors about one common rotation vector. In this case rotating the primary x-, y-, z-
    axes and the actor's pointing vector.

    Args:
        x (np.ndarray): x-axis
        y (np.ndarray): y-axis
        z (np.ndarray): z-axis
        p (np.ndarray): pointing vector
        angle (np.ndarray): rotation vector with magnitude being the rotation angle

    Returns:
        rotated x-, y-, z- axes and pointing vector
    """
    x = rodrigues_rotation(x, angle)
    y = rodrigues_rotation(y, angle)
    z = rodrigues_rotation(z, angle)
    p = rodrigues_rotation(p, angle)

    return x, y, z, p
