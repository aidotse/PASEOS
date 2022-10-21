"""This file contains models of the battery discharge due to power consumption"""


def discharge(
    actor,
    power_consumption_in_Ws: float,
    battery_model="simple",
):
    """Models the reduction of battery energy on the actor

    Args:
        actor (SpacecraftActor): Actor to apply this
        power_consumption_in_Ws (float): Consumed power in Ws
        battery_model (str, optional): Defines which model to use, atm only "simple". Defaults to "simple".

    Returns:
        SpacecraftActor: Modified actor after power consumption.
    """

    if battery_model == "simple":
        if actor._battery_level_in_Ws < power_consumption_in_Ws:
            raise ValueError(
                "Insufficient Battery. Actor "
                + str(actor)
                + " has battery level: "
                + str(actor._battery_level_in_Ws)
                + " - trying to discharge "
                + str(power_consumption_in_Ws)
            )
        else:
            actor._battery_level_in_Ws -= power_consumption_in_Ws
            return actor
    else:
        raise NotImplementedError("Unknown battery model " + battery_model)
