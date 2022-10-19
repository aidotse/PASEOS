"""This file contains models of the communication transmission through a channel"""

import pykep as pk
from loguru import logger


def get_communication_window(
    local_actor,
    local_actor_communication_link_name,
    target_actor,
    dt: float,
    t0: pk.epoch,
    data_to_send_in_b: int,
    window_timeout_value_in_s=7200,
):
    """Returning the communication window and the amount of data that can be transmitted from the local to the target actor.

    Args:
        local_actor (base_actor): local actor.
        local_actor_communication_link_name (base_actor):  name of the local_actor's communication link to use.
        target_actor (base_actor): other actor.
        dt (float): simulation timestep [s].
        t0 (pk.epoch): current simulation time.
        data_to_send_in_b (int): amount of data to transmit [b].
        window_timeout_value_in_s (float, optional): timeout for estimating the communication window. Defaults to 7200.0.
    Returns:
        pk.epoch: communication window start time.
        pk.epoch: communication window end time.
        int: data that can be transmitted in the communication window [b].
    """

    assert local_actor_communication_link_name in local_actor._communication_links, (
        "Trying to use a not-existing communication link with the name: "
        + local_actor._communication_links
    )
    local_actor_comm_link = local_actor._communication_links[
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
