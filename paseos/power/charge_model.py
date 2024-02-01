"""This file contains models of the battery charge via e.g. solar power"""
from loguru import logger
import pykep as pk

from paseos.power.power_device_type import PowerDeviceType


def charge(
    actor,
    charging_time_in_s: float,
    model="simple",
):
    """Models the charging via solar panels or similar.

    Args:
        actor (SpacecraftActor): Actor to apply this to.
        charging_time_in_s (float): Charging period in s.
        model (str, optional): Model to use, at the moment only "simple". Defaults to "simple".

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

    # Compute end of charging time
    t1 = pk.epoch(actor.local_time.mjd2000 + charging_time_in_s * pk.SEC2DAY)

    # If solar panels are used, check for eclipse
    if actor.power_device_type == PowerDeviceType.SolarPanel:
        # Check for eclipse at start / end
        if actor.is_in_eclipse() or actor.is_in_eclipse(t1):
            logger.debug("Actor is in eclipse, not charging.")
            return actor

    # Apply specified charging model
    if model == "simple":
        actor._battery_level_in_Ws += actor._charging_rate_in_W * charging_time_in_s
        actor._battery_level_in_Ws = min(
            actor.battery_level_in_Ws, actor._max_battery_level_in_Ws
        )
        return actor
    else:
        raise NotImplementedError("Unknown charging model " + model)
