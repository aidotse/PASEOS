"""this file contains functions that return attitude disturbance torque vectors expressed in the actor body frame"""

# OUTPUT NUMPY ARRAYS
# OUTPUT IN BODY FRAME
import numpy as np
from ..utils.reference_frame_transfer import (
    rpy_to_body,
    eci_to_rpy,
    compute_transformation_matrix_rpy_body,
)


def compute_aerodynamic_torque(r, v, mesh, actor_attitude_in_rad, current_spacecraft_temperature_K):
    """Calculates the aerodynamic torque on the satellite.
    The model used is taken from "Roto-Translational Spacecraft Formation Control Using Aerodynamic Forces"; Ran. S,
    Jihe W., et al.; 2017. The mass density of the atmosphere is calculated from the best linear fit of the data
    extracted from "Thermospheric mass density: A review"; Emmert J.T.; 2015. This function only works for Earth
    centered orbits and satellites defined by a cuboid mesh as in the geometrical model.

    Future addition to the model can be the temperature of the spacecraft as an input parameter. At the moment the
    temperature of the spacecraft is assumed in the model. The sensitivity of the torque with respect to the
    temperature of the spacecraft and of the gas is low.

    Args:
        r (np.array): distance from the satellite and the Earth's center of mass [km].
        v (np.array): velocity of the satellite in ECI reference frame [m/s].
        mesh (trimesh): mesh of the satellite from the geometric model.
        actor_attitude_in_rad (np.array): spacecraft actor in rad.
        current_spacecraft_temperature_K (float): current temperature in Kelvin.
     Returns:
         T (np.array): torque vector in the spacecraft body frame.
    """
    # Constants for aerodynamic coefficients calculation
    temperature_gas = 1000  # [K]
    R = 8.314462  # Universal Gas Constant, [J/(K mol)]
    altitude = np.linalg.norm(r) - 6371  # [km]
    density = 10 ** (
        -(altitude + 1285) / 151
    )  # equation describing the best linear fit for the data, [kg/m^3]
    molecular_speed_ratio_t = np.linalg.norm(v) / np.sqrt(
        2 * R * temperature_gas
    )  # Used in the Cd and Cl calculation
    molecular_speed_ratio_r = np.linalg.norm(v) / np.sqrt(
        2 * R * current_spacecraft_temperature_K
    )  # Used in the Cd and Cl calculation
    accommodation_parameter = 0.85

    #  Get the normal vectors of all the faces of the mesh in the spacecraft body reference frame, and then they get
    #  translated in the Roll Pitch Yaw frame with a transformation from paseos.utils.reference_frame_transfer.py
    face_normals_sbf = mesh.face_normals[0:12]
    # Get ntransformation matrix
    transformation_matrix_rpy_body = compute_transformation_matrix_rpy_body(actor_attitude_in_rad)
    face_normals_rpy = np.dot(transformation_matrix_rpy_body, face_normals_sbf.T).T

    #  Get the velocity and transform it in the Roll Pitch Yaw frame. Get the unit vector associated with the latter
    v_rpy = eci_to_rpy(v, r, v)
    unit_v_rpy = v_rpy / np.linalg.norm(v_rpy)

    #  Loop to get the normals, the areas, the angle of attack and the centroids of the faces with airflow, confronting them
    #  with the velocity vector direction.
    #  If the dot product between velocity and normal is positive, the plate corresponding to the normal is receiving
    #  airflow and is stored in the variable normals_faces_with_airflow. Similarly, the areas of the faces is stored in
    #  area_faces_airflow, and the angles of attack of the respective faces in alpha. The last three lines calculate the
    #  centroids of the faces that receive airflow, for later use in the torque calculation.

    #  Initialize parameters and variables for the for loop.
    j = 0
    normals_faces_with_airflow = np.zeros((6, 3))  # Maximum six faces have airflow
    alpha = [
        0,
        0,
        0,
        0,
        0,
        0,
    ]  # angle of attack matrix, stores the angles of attack in radiant
    area_all_faces_mesh = mesh.area_faces  # ordered list of all faces' areas
    area_faces_airflow = [0, 0, 0, 0, 0, 0]
    centroids_faces_airflow = [0, 0, 0, 0, 0, 0]

    for i in range(12):
        if np.dot(face_normals_rpy[i], v_rpy) > 0:
            normals_faces_with_airflow[j] = face_normals_rpy[i]
            area_faces_airflow[j] = area_all_faces_mesh[
                i
            ]  # get the area of the plate [i] which is receiving airflow
            alpha[j] = np.arccos(np.dot(normals_faces_with_airflow[j], unit_v_rpy))
            face_vertices = mesh.vertices[mesh.faces[i]]
            face_vertices_rpy = np.dot(
                np.linalg.inv(transformation_matrix_rpy_body), face_vertices.T
            ).T
            centroids_faces_airflow[j] = np.mean(
                face_vertices_rpy, axis=0
            )  # get the centroids of the face[i] with airflow
            j += 1

    #  Get the aerodynamic coefficient Cd and Cl for every plate and calculate the corresponding drag and lift forces
    #  for every plate [k] with airflow. Calculate the torque associated with the forces with the previously calculated
    #  centroid position of every plate.

    # Initialization of the variables
    force_drag = [0, 0, 0, 0, 0, 0]
    force_lift = [0, 0, 0, 0, 0, 0]
    torque_aero = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
    alpha = np.array(alpha)

    for k in range(j):
        alpha_scalar = alpha[k]
        C_d = (
            1
            / molecular_speed_ratio_t**2
            * (
                molecular_speed_ratio_t
                / np.sqrt(np.pi)
                * (
                    4 * np.sin(alpha_scalar) ** 2
                    + 2 * accommodation_parameter * np.cos(2 * alpha_scalar)
                )
                * np.exp(-((molecular_speed_ratio_t * np.sin(alpha_scalar)) ** 2))
                + np.sin(alpha_scalar)
                * (
                    1
                    + 2 * molecular_speed_ratio_t**2
                    + (1 - accommodation_parameter)
                    * (1 - 2 * molecular_speed_ratio_t**2 * np.cos(2 * alpha_scalar))
                )
                * np.math.erf(molecular_speed_ratio_t * np.sin(alpha_scalar))
                + accommodation_parameter
                * np.sqrt(np.pi)
                * molecular_speed_ratio_t**2
                / molecular_speed_ratio_r
                * np.sin(alpha_scalar) ** 2
            )
        )

        C_l = (
            np.cos(alpha[k])
            / molecular_speed_ratio_t**2
            * (
                2
                / np.sqrt(np.pi)
                * (2 - 2 * accommodation_parameter)
                * molecular_speed_ratio_t
                * np.sin(alpha_scalar)
                * np.exp(-((molecular_speed_ratio_t * np.sin(alpha_scalar)) ** 2))
                + (
                    2
                    * (2 - 2 * accommodation_parameter)
                    * (molecular_speed_ratio_t * np.sin(alpha_scalar)) ** 2
                    + (2 - accommodation_parameter)
                )
                * np.math.erf(molecular_speed_ratio_t * np.sin(alpha_scalar))
                + accommodation_parameter
                * np.sqrt(np.pi)
                * molecular_speed_ratio_t**2
                / molecular_speed_ratio_r
                * np.sin(alpha_scalar)
            )
        )

        # Drag force on the plate [k]. Direction along the velocity vector.
        force_drag[k] = (
            -0.5 * density * C_d * area_faces_airflow[k] * np.linalg.norm(v) ** 2 * unit_v_rpy
        )
        # Lift force on the plate [k]. Direction along the (v x n) x v direction, lift vector defined to be in that
        # direction. Intermediate step to get v x n.
        v_x_n_vector = np.cross(unit_v_rpy, normals_faces_with_airflow[k])
        not_norm_lift_vector = np.cross(v_x_n_vector, unit_v_rpy)
        lift_vector = not_norm_lift_vector / np.linalg.norm(not_norm_lift_vector)
        force_lift[k] = (
            -0.5 * density * C_l * area_faces_airflow[k] * np.linalg.norm(v) ** 2 * lift_vector
        )

        # Torque calculated as the product between the distance of the centroid from the geometric center of the
        # satellite and the sum of the forces.
        torque_aero[k] = np.cross(
            centroids_faces_airflow[k] - mesh.centroid,
            (np.array(force_drag[k]) + np.array(force_lift[k])),
        )

    #  Compute aero torque in the timestep as the vector sum of all the torques
    torque_aero = np.array(torque_aero)
    T_rpy = torque_aero.sum(axis=0)
    T = transformation_matrix_rpy_body @ T_rpy
    T[np.isnan(T)] = 0  # substitutes 0 to any NaN value

    return np.array(T)


def compute_gravity_gradient_torque(central_body, u_r, u_n, J, r):
    """
    Equation for gravity gradient torque with up to J2 effect from:
    https://doi.org/10.1016/j.asr.2018.06.025, chapter 3.3
    This function currently only works for Earth centered orbits.

    Args:
        u_r (np.array): Unit vector pointing from Satellite center of gravity to Earth's center of gravity.
        u_n (np.array): Unit vector along the Earth's rotation axis, in the spacecraft body frame.
        J (np.array): The satellites moment of inertia, in the form of [[Ixx Ixy Ixz]
                                                                        [Iyx Iyy Iyx]
                                                                        [Izx Izy Izz]].
        r (float): The distance from the center of the Earth to the satellite.

    Returns:
        np.array: total gravitational torques in Nm expressed in the spacecraft body frame.
    """
    # Constants
    mu = central_body.mu_self  # Earth's gravitational parameter, [m^3/s^2].
    # Earth's J2 coefficient [https://ocw.tudelft.nl/wp-content/uploads/AE2104-Orbital-Mechanics-Slides_8.pdf].
    J2 = 1.0826267e-3
    Re = central_body.radius  # Earth's radius, [m]

    tg_term_1 = (3 * mu / (r**3)) * np.cross(u_r, np.dot(J, u_r))
    tg_term_2 = (
        30 * np.dot(u_r, u_n) * (np.cross(u_n, np.dot(J, u_r)) + np.cross(u_r, np.dot(J, u_n)))
    )
    tg_term_3 = np.cross((15 - 105 * np.dot(u_r, u_n) ** 2) * u_r, np.dot(J, u_r)) + np.cross(
        6 * u_n, np.dot(J, u_n)
    )
    tg = tg_term_1 + mu * J2 * Re**2 / (2 * r**5) * (tg_term_2 + tg_term_3)
    return np.array(tg)


def compute_magnetic_torque(m_earth, m_sat, position, velocity, attitude):
    """Calculates the external disturbance torque acting on the actor due to the magnetic field of the earth.
    a dipole magnetic field flux density is described by the formula: B = μ0/(4πr³) * [3 r_hat(r_hat ⋅ m) − m].
    With μ0 = 4 π 1e-7 H/m (vacuum permeability), r = actor distance from dipole center, r_hat = unit position vector,
    and m the magnetic dipole moment vector of the Earth (magnitude in the year 2000 = 7.79 x 10²² Am²).

    The disturbance torque is then calculated by: T = m_sat x B.
    With m_sat the (residual) magnetic dipole moment vector of the actor, magnitude usually between 0.1 - 20 Am² (SMAD).

    https://en.wikipedia.org/wiki/Magnetic_dipole (or Chow, Tai L. (2006). Introduction to electromagnetic theory:
    a modern perspective, used formular on p. 149).

    Args:
        m_earth (np.ndarray): magnetic dipole moment vector of the Earth in Am².
        m_sat (np.ndarray): magnetic dipole moment vector of the actor, magnitude usually between 0.1 - 20 Am².
        position (tuple or np.ndarray): actor position.
        velocity (tuple or np.ndarray): actor velocity (used for frame transformation).
        attitude (np.ndarray): actor velocity (used for frame transformation).

    Returns: Disturbance torque vector T (nd.array) in Nm in the actor body frame.
    """
    # convert to np.ndarray.
    position = np.array(position)
    velocity = np.array(velocity)

    # actor distance.
    r = np.linalg.norm(position)
    # actor unit position vector.
    r_hat = position / r

    # magnetic field flux density at actor's position in Earth inertial frame.
    B = 1e-7 * (3 * np.dot(m_earth, r_hat) * r_hat - m_earth) / (r**3)

    # transform field vector to body frame.
    B = rpy_to_body(eci_to_rpy(B, position, velocity), attitude)

    # disturbance torque.
    T = np.cross(m_sat, B)
    return T
