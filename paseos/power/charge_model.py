"""This file contains models of the battery charge via e.g. solar power"""


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
    assert charging_time_in_s > 0, "Charging time has to be positive."
    if model == "simple":
        actor.battery_level_in_Ws += actor._charging_rate_in_W * charging_time_in_s
        actor.battery_level_in_Ws = min(
            actor.battery_level_in_Ws, actor._max_battery_level_in_Ws
        )
        return actor
    else:
        raise NotImplementedError("Unknown charging model " + model)
