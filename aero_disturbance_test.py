from paseos.attitude.disturbance_calculations import calculate_aero_torque
from paseos.utils.reference_frame_transfer import transformation_matrix_rpy_body
import trimesh
import numpy as np
"""
Getting the data to run the function
"""


""" Actual tests:

Test zero: get the Cd of the single plates and weigh it against the Cd often used in missions: Cd=2 
Done modifying the function to print Cd value. 

Verified for a set 3 different altitudes and satellite's attitudes 
Cd values obtained in [0.02 and 2.31], low Cd values correspond to low values of the angle of attack
"""

"""
First test uses existing spacecraft data to check that with the same initial conditions the torque exerted on the 
satellite is comparable to the real data. For example GOCE data reveal that the aerodynamic torque levels are in the
order of 10^-3 - 10^-4 for a axially symmetric satellite of 5x2 m. We can expect torques in the order of 10^-4  
in magnitude for a cuboid satellite 1x1 m at the same altitude as GOCE (255 km).
"""
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
# GOCE orbital altitude and speed
r = np.array([6626, 0, 0]) #6626
v = np.array([0, 7756, 0])
temperature_t = 1000

transformation_matrix = transformation_matrix_rpy_body(np.array([0, np.pi/4, np.pi/4]))

T = calculate_aero_torque(r, v, mesh, temperature_t, transformation_matrix)
abs_T = np.linalg.norm(T)*10**3

# print("Total torque is ", abs_T, "mN")
# print("The expected torque is in the order of 10^-4")

if 10**-4 < abs_T/10**3 < 10**-3:
    print("Test 1 passed")
else:
    print("Test 1 not passed")


"""
Second test aims to model simple cases and verify that the torque exerted matches the expected torque calculated by the 
function, with particula emphasis on the torque vector direction.
"""

#  Base case: RPY frame is aligned with Body Frame. There should be no torque.
transformation_matrix = transformation_matrix_rpy_body(np.array([0, 0, 0]))  # can change the euler angles if willing
T = calculate_aero_torque(r, v, mesh, temperature_t, transformation_matrix)
if np.linalg.norm(T) < 10**(-4):
    print("Test 2.1 passed")
else:
    print("Test 2.1 not passed")

#  Cases of simple rotations
#  First case, satellite with an attitude that yields a torque vector parallel to [0, -1, 0].
transformation_matrix = transformation_matrix_rpy_body(np.array([0, np.pi/6, 0]))
T = calculate_aero_torque(r, v, mesh, temperature_t, transformation_matrix)
similarity = np.dot(T,[0, 1, 0])
if similarity == np.linalg.norm(T):
    print("Test 2.2 passed")
else:
    print("Test 2.2 not passed")

#  Second case, satellite with an attitude that yields zero torque
transformation_matrix = transformation_matrix_rpy_body(np.array([np.pi/6, 0, 0]))
T = calculate_aero_torque(r, v, mesh, temperature_t, transformation_matrix)
if all(T) == 0:
    print("Test 2.3 passed")
else:
    print("Test 2.3 not passed")

#  Third case, positive rotation of 30° about the z-axis, expected torque in positive z-axis direction
transformation_matrix = transformation_matrix_rpy_body(np.array([0, 0, np.pi/6]))
T = calculate_aero_torque(r, v, mesh, temperature_t, transformation_matrix)
similarity = np.dot(T, [0, 0, 1])

if similarity == np.linalg.norm(T):
    print("Test 2.4 passed")
else:
    print("Test 2.4 not passed")
