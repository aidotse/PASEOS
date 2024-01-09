# this functions could be implemented inside the attitude model class but I'd rather have it
# separately right now.

# OUTPUT NUMPY ARRAYS
import numpy as np


def calculate_aero_torque():
    # calculations for torques
    # T must be in actor body fixed frame (to be discussed)
    T = [0, 0, 0]
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
