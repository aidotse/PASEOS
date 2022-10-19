"""This file contains models of the communication transmission through a channel"""

import pykep as pk
from loguru import logger

def check_communication_link(
    local_actor,
    local_actor_communication_link_name,
    actor,
    dt: float,
    t0: float,
    data_to_send_in_b: int,
    window_timeout_value_in_s=7200
):
    """Checks how much data can be transmitted over the communication link and the length of the communication link.

    Args:
        local_actor (base_actor): local actor.
        local_actor_communication_link_name (base_actor):  name of the local_actor's communication link to use.
        actor (base_actor): other actor.
        dt (float): simulation timestep [s].
        t0 (float): current simulation time [s].
        data_to_send_in_b (int): amount of data to transmit [b].
        window_timeout_value_in_s (float, optional): timeout value for the estimation of communication window. Defaults to 7200.0.

    Returns:
        int: remaining amount of data to transmit [b].
        float: length of the remaining communication window [s].
    """
    local_actor_comm_link = local_actor._communication_links[
        local_actor_communication_link_name
    ]

    assert local_actor_comm_link.bandwidth_in_kbps > 0, "Bandiwidth has to be positive."

    transmitted_data_b = 0
    tk = t0
    while (local_actor.is_in_line_of_sight(actor, pk.epoch(tk * pk.SEC2DAY))) and (tk - t0 < window_timeout_value_in_s):
        tk += dt
        transmitted_data_b += (
            int(local_actor_comm_link.bandwidth_in_kbps * dt) * 1000
        )  # (This is the quantum of information that you can transmit)

    if tk - t0 >= window_timeout_value_in_s:
        logger.debug(
            "Timeout reached for the estimation of the communication window.")

    return max(data_to_send_in_b - transmitted_data_b, 0), tk - t0
