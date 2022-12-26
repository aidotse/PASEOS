import pykep as pk
from loguru import logger

from .get_communication_window import get_communication_window


def find_next_window(
    local_actor,
    link_name: str,
    target_actor,
    search_window_in_s: float,
    t0: pk.epoch,
    search_step_size: float = 10,
):
    """Returns the start time of the next window in the given timespan (if any).

    Args:
        local_actor (BaseActor): Actor to find window from.
        link_name (str): Name of the comm device.
        target_actor (BaseActor): Actor find window with.
        search_window_in_s (float): Size of the search window in s.
        t0 (pk.epoch): Start time of the search.
        search_step_size (float): Size of steps in the search. Defaults to 10.

    Returns:
        Window start (pk.epoch), window length (float [s]), data (int [b]). None,0,0 if none found.
    """
    logger.debug(f"Find next comms window between {local_actor} and {target_actor}")

    assert link_name in local_actor.communication_devices, (
        "Trying to use a not-existing communication link with the name: "
        + local_actor.communication_devices
    )
    local_actor_comm_link = local_actor.communication_devices[link_name]

    assert local_actor_comm_link.bandwidth_in_kbps > 0, "Bandiwidth has to be positive."
    assert search_step_size > 0, "dt has to be positive."

    # Compute start and end of the search window
    t = t0.mjd2000 * pk.DAY2SEC
    end = t + search_window_in_s

    # Move forward in time until either search window ends
    # or we find a window
    while t < end:
        current_epoch = pk.epoch(t * pk.SEC2DAY)
        win_start, win_end, transmittable_data = get_communication_window(
            local_actor=local_actor,
            local_actor_communication_link_name=link_name,
            target_actor=target_actor,
            dt=10,
            t0=current_epoch,
        )
        win_length = win_end.mjd2000 - win_start.mjd2000
        if win_length > 0:
            return win_start, win_length * pk.DAY2SEC, transmittable_data
        t = t + search_step_size

    return None, 0, 0
