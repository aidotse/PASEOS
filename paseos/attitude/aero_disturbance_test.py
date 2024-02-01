from paseos.attitude.disturbance_calculations import calculate_aero_torque
from paseos.utils.reference_frame_transfer import transformation_matrix_rpy_body
import trimesh
import numpy as np


#  create mesh
vertices = [
[-0.5, -0.5, -0.5],
[-0.5, -0.5, 0.5],
[-0.5, 0.5, -0.5],
[-0.5, 0.5, 0.5],
[0.5, -0.5, -0.5],
[0.5, -0.5, 0.5],
[0.5, 0.5, -0.5],
[0.5, 0.5, 0.5],
]
faces = [
[0, 1, 3],
[0, 3, 2],
[0, 2, 6],
[0, 6, 4],
[1, 5, 3],
[3, 5, 7],
[2, 3, 7],
[2, 7, 6],
[4, 6, 7],
[4, 7, 5],
[0, 4, 1],
[1, 4, 5],
]
mesh = trimesh.Trimesh(vertices, faces)


def test_1():
    """ First test uses existing spacecraft data to check that with the same initial conditions the torque exerted on the
        satellite is comparable to the real GOCE data. Goce has a cross-section of 1.1 m^2 and during it's drag free
        phase experienced between 1 and 20 mN of drag force. It is reasonable to expect a torque in the same order of
        magnitude for a satellite of 1x1x1 m^2 at the same altitude as GOCE.
    """
    # GOCE orbital altitude and speed
    r = np.array([6626, 0, 0])  # [km]
    v = np.array([0, 7756, 0])  # [m/s]

    transformation_matrix = transformation_matrix_rpy_body(np.array([np.pi/4, np.pi/6, 0]))

    T = calculate_aero_torque(r, v, mesh, transformation_matrix)
    abs_T = np.linalg.norm(T)

    assert 5*10**-4 < abs_T < 2*10**-2

def test_2a():
    """ Second tests aim to model simple cases and verify that the torque exerted matches the expected torque calculated
        by the function, with particular emphasis on the torque vector direction.

        Base case: RPY frame is aligned with Body Frame. There should be no torque.
    """
    # Circular orbit at GOCE altitude
    r = np.array([6626, 0, 0])  # [km]
    v = np.array([0, 7756, 0])  # [km]

    transformation_matrix = transformation_matrix_rpy_body(np.array([0, 0, 0]))  # can change the euler angles if willing
    T = calculate_aero_torque(r, v, mesh, transformation_matrix)

    assert np.linalg.norm(T) < 10**(-8)

def test_2b():
    """ Second tests aim to model simple cases and verify that the torque exerted matches the expected torque calculated
        by the function, with particular emphasis on the torque vector direction.

        Second case, satellite with an attitude that yields a torque vector parallel to [0, -1, 0]
    """
    # Circular orbit at GOCE altitude
    r = np.array([6626, 0, 0])  # [km]
    v = np.array([0, 7756, 0])  # [km]

    transformation_matrix = transformation_matrix_rpy_body(np.array([0, np.pi/6, 0]))
    T = calculate_aero_torque(r, v, mesh, transformation_matrix)
    similarity = np.dot(T,[0, 1, 0])

    assert similarity == np.linalg.norm(T)

def test_2c():
    """ Second tests aim to model simple cases and verify that the torque exerted matches the expected torque calculated
        by the function, with particular emphasis on the torque vector direction.

        Third case, satellite with an attitude that yields zero torque
    """
    # Circular orbit at GOCE altitude
    r = np.array([6626, 0, 0])  # [km]
    v = np.array([0, 7756, 0])  # [km]

    transformation_matrix = transformation_matrix_rpy_body(np.array([np.pi/6, 0, 0]))
    T = calculate_aero_torque(r, v, mesh, transformation_matrix)

    assert all(T) == 0

def test_2d():
    """ Second tests aim to model simple cases and verify that the torque exerted matches the expected torque calculated
        by the function, with particular emphasis on the torque vector direction.

        Third case, positive rotation of 30° about the z-axis, expected torque in the positive z-axis direction.
    """
    # Circular orbit at GOCE altitude
    r = np.array([6626, 0, 0])  # [km]
    v = np.array([0, 7756, 0])  # [km]

    transformation_matrix = transformation_matrix_rpy_body(np.array([0, 0, np.pi/6]))
    T = calculate_aero_torque(r, v, mesh, transformation_matrix)
    similarity = np.dot(T, [0, 0, 1])

    assert similarity == np.linalg.norm(T)
