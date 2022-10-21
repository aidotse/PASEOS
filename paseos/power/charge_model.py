"""This file contains models of the battery charge via e.g. solar power"""
from loguru import logger


def charge(
    actor,
    charging_time_in_s: float,
    model="simple",
):
    """Models the charging via solar panels or similar.

    Args:
        actor (SpacecraftActor): Actor to apply this to.
        charging_time_in_s (float): Charging period in s.
        model (str, optional): Model to use, amt only "simple". Defaults to "simple".

    Returns:
        SpacecraftActor: Modified actor after charging.
    """
    logger.trace(
        "Charging actor"
        + str(actor)
        + " for "
        + str(charging_time_in_s)
        + " seconds using model "
        + model
    )
    assert charging_time_in_s > 0, "Charging time has to be positive."

    if model == "simple":
        actor._battery_level_in_Ws += actor._charging_rate_in_W * charging_time_in_s
        actor._battery_level_in_Ws = min(
            actor._battery_level_in_Ws, actor._max_battery_level_in_Ws
        )
        return actor
    else:
        raise NotImplementedError("Unknown charging model " + model)
