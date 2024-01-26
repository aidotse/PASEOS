# this functions could be implemented inside the attitude model class but I'd rather have it
# separately right now.

# OUTPUT NUMPY ARRAYS
import numpy as np
import trimesh

from paseos.utils.reference_frame_transfer import transformation_matrix_eci_rpy, transformation_matrix_rpy_body, \
   eci_to_rpy



def calculate_aero_torque(r,v,mesh,temperature_spacecraft, transformation_matrix_rpy_body,):
    """ Calculates the aerodynamic torque on the satellite. Possible further inputs are temperature_spacecraft from the
    thermal model.
     Returns:
         T: torque vector in the spacecraft body frame
    """

    #  Set data useful for aerodynamic coefficients calculation
    temperature_spacecraft = 300  # [K]  we could connect this with the thermal model
    temperature_gas = 1000  # [K]  valid for upper stratosphere, could be completely wrong higher up
    altitude = np.linalg.norm(r)-6371  # [km]
    density = 10**(-(altitude+1285)/151)  # from data fit from thermospheric mass density
    R = 8.314462  # [J/(K mol)] Universal Gas Constant
    molecular_speed_ratio_t = np.linalg.norm(v)/np.sqrt(2*R*temperature_gas)  # Used in the Cd and Cl calculation
    molecular_speed_ratio_r = np.linalg.norm(v)/np.sqrt(2*R*temperature_spacecraft)  # Used in the Cd and Cl calculation
    accommodation_parameter = 0.85

    #  Get the normal vectors of all the faces of the mesh in the spacecraft body reference frame, and then they get
    #  translated in the Roll Pitch Yaw frame with a transformation from paseos.utils.reference_frame_transfer.py
    face_normals_sbf = mesh.face_normals[0:12]
    face_normals_rpy = np.dot(transformation_matrix_rpy_body, face_normals_sbf.T).T  # Check  transposition

    #  Get the velocity and transform it in the Roll Pitch Yaw frame. Get the unit vector associated with the latter
    v_rpy = eci_to_rpy(v, r, v)
    unit_v_rpy = v_rpy/np.linalg.norm(v_rpy)

    #  Get the normals, the areas, the angle of attack and the centroids of the faces with airflow, confronting them
    #  with the velocity vector direction. If the dot product between velocity and normal is positive, the plate
    #  corresponding to the normal is receiving airflow.

    #  Initialize parameters and variables for the for loop.
    j = 0
    normals_faces_with_airflow = np.zeros((6, 3))  # Maximum six faces have airflow
    alpha = [0, 0, 0, 0, 0, 0]  # angle of attack matrix, stores the angles of attack in radiant
    area_all_faces_mesh = mesh.area_faces  # ordered list of all faces' areas
    area_faces_airflow = [0, 0, 0, 0, 0, 0]
    centroids_faces_airflow = [0, 0, 0, 0, 0, 0]

    for i in range(12):
        if np.dot(face_normals_rpy[i], v_rpy) > 0:
            normals_faces_with_airflow[j] = face_normals_rpy[i]
            area_faces_airflow[j] = area_all_faces_mesh[i]  # get the area of the plate [i] which is receiving airflow
            face_vertices = mesh.vertices[mesh.faces[j]]
            centroids_faces_airflow[j] = np.mean(face_vertices, axis=0)  # get the centroids of the face[i] with airflow
            alpha[j] = np.arccos(np.dot(normals_faces_with_airflow[j], unit_v_rpy))
            j += 1

    #  Get the aerodynamic coefficient Cd and Cl for every plate and calculate the corresponding drag and lift forces
    #  for every plate [k] with airflow. Calculate the torque associated with the forces with the previously calculated
    #  centroid position of every plate.

    # Initialization of the variables
    force_drag = [0, 0, 0, 0, 0, 0]
    force_lift = [0, 0, 0, 0, 0, 0]
    torque_aero = [[0, 0, 0],
                   [0, 0, 0],
                   [0, 0, 0],
                   [0, 0, 0],
                   [0, 0, 0],
                   [0, 0, 0]]
    alpha = np.array(alpha)

    for k in range(j):
        alpha_scalar = alpha[k]
        C_d = 1/molecular_speed_ratio_t**2 * (molecular_speed_ratio_t / np.sqrt(np.pi) * \
            (4 * np.sin(alpha_scalar)**2 + 2 * accommodation_parameter * np.cos(2*alpha_scalar)) * \
            np.exp(-(molecular_speed_ratio_t*np.sin(alpha_scalar))**2) + np.sin(alpha_scalar) * \
            (1 + 2 * molecular_speed_ratio_t ** 2 + (1 - accommodation_parameter) * \
            (1 - 2 * molecular_speed_ratio_t ** 2 * np.cos(2 * alpha_scalar))) * \
            np.math.erf(molecular_speed_ratio_t * np.sin(alpha_scalar)) + accommodation_parameter * np.sqrt(np.pi)* \
            molecular_speed_ratio_t ** 2 / molecular_speed_ratio_r * np.sin(alpha_scalar) ** 2)

        C_l = np.cos(alpha[k]) / molecular_speed_ratio_t**2 * (2 / np.sqrt(np.pi) * (2-2*accommodation_parameter) * \
            molecular_speed_ratio_t*np.sin(alpha_scalar)*np.exp(-(molecular_speed_ratio_t*np.sin(alpha_scalar))**2)+\
            (2*(2-2*accommodation_parameter)*(molecular_speed_ratio_t*np.sin(alpha_scalar))**2 + \
            (2-accommodation_parameter)) * np.math.erf(molecular_speed_ratio_t*np.sin(alpha_scalar)) + \
            accommodation_parameter*np.sqrt(np.pi) * molecular_speed_ratio_t**2 / molecular_speed_ratio_r * \
            np.sin(alpha_scalar))

        # Drag force on the plate [k]. Direction along the velocity vector.
        force_drag[k] = - 0.5 * density * C_d * area_faces_airflow[k] * np.linalg.norm(v)**2 * unit_v_rpy
        # Lift force on the plate [k]. Direction along the (v x n) x v vector. Intermediate step to get v x n.
        v_x_n_vector = np.cross(unit_v_rpy, normals_faces_with_airflow[k])
        force_lift[k] = - 0.5 * density * C_l * area_faces_airflow[k] * np.linalg.norm(v)**2 * np.cross(v_x_n_vector, unit_v_rpy)

        # Torque calculated as the product between the distance of the centroid from the geometrica center of the
        # satellite and the sum of the forces.
        torque_aero[k] = np.cross(centroids_faces_airflow[k]-mesh.centroid, (np.array(force_drag[k]) + np.array(force_lift[k])))

    #  Compute aero torque in the timestep as the vector sum of all the torques
    torque_aero = np.array(torque_aero)
    T_rpy = torque_aero.sum(axis=0)
    T = transformation_matrix_rpy_body @ T_rpy
    return np.array(T)


def calculate_grav_torque():
    # calculations for torques
    # T must be in actor body fixed frame (to be discussed)
    T = [0, 0, 0]
    return np.array(T)


def calculate_magnetic_torque():
    # calculations for torques
    # T must be in actor body fixed frame (to be discussed)
    T = [0, 0, 0]
    return np.array(T)
