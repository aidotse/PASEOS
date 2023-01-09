"""This file contains models of the communication transmission through a channel"""

import sys

import pykep as pk
from loguru import logger

from ..actors.base_actor import BaseActor


def get_communication_window(
    local_actor: BaseActor,
    local_actor_communication_link_name: str,
    target_actor: BaseActor,
    dt: float = 10.0,
    t0: pk.epoch = None,
    data_to_send_in_b: int = sys.maxsize,
    window_timeout_value_in_s=7200,
):
    """Returning the communication window and the amount of data that can be transmitted from the local to the target actor.

    Args:
        local_actor (BaseActor): Local actor.
        local_actor_communication_link_name (str):  Name of the local_actor's communication link to use.
        target_actor (BaseActor): other actor.
        dt (float): Simulation timestep [s]. Defaults to 10.
        t0 (pk.epoch): Current simulation time. Defaults to local time.
        data_to_send_in_b (int): Amount of data to transmit [b]. Defaults to maxint.
        window_timeout_value_in_s (float, optional): Timeout for estimating the communication window. Defaults to 7200.0.
    Returns:
        pk.epoch: Communication window start time.
        pk.epoch: Communication window end time.
        int: Data that can be transmitted in the communication window [b].
    """
    logger.debug(f"Computing comms window between {local_actor} and {target_actor}")

    if t0 is None:
        t0 = local_actor.local_time

    assert local_actor_communication_link_name in local_actor.communication_devices, (
        "Trying to use a not-existing communication link with the name: "
        + local_actor.communication_devices
    )
    local_actor_comm_link = local_actor.communication_devices[
        local_actor_communication_link_name
    ]

    assert local_actor_comm_link.bandwidth_in_kbps > 0, "Bandiwidth has to be positive."
    assert dt > 0, "dt has to be positive."
    assert data_to_send_in_b > 0, "data_to_send_in_b has to be positive."

    # Getting t0 in s
    t0_in_s = (t0.mjd2000 - pk.epoch(0).mjd2000) / pk.SEC2DAY
    transmitted_data_in_b = 0
    current_time_in_s = t0_in_s
    while (
        local_actor.is_in_line_of_sight(
            target_actor, pk.epoch(current_time_in_s * pk.SEC2DAY)
        )
    ) and (current_time_in_s - t0_in_s < window_timeout_value_in_s):
        current_time_in_s += dt
        transmitted_data_in_b += int(
            local_actor_comm_link.bandwidth_in_kbps * dt * 1000
        )  # (This is the quantum of information that you can transmit)

    if current_time_in_s - t0_in_s >= window_timeout_value_in_s:
        logger.debug("Timeout reached for the estimation of the communication window.")

    return (
        t0,
        pk.epoch(current_time_in_s * pk.SEC2DAY),
        min(transmitted_data_in_b, data_to_send_in_b),
    )
