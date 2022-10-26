from loguru import logger
from dotmap import DotMap

from paseos.actors.base_actor import BaseActor


class ActivityManager:
    """This class is used to handle registering, performing and collection of activities. There can only be one instance of it and each paseos instance has one."""

    def __new__(self):
        if not hasattr(self, "instance"):
            self.instance = super(ActivityManager, self).__new__(self)
        else:
            logger.debug(
                "Tried to create another instance of ActivityManager. Keeping original one..."
            )
        return self.instance

    def __init__(self):
        logger.trace("Initializing ActivityManager")
        self._activities = DotMap(_dynamic=False)

    def register_activity(
        self,
        name: str,
        requires_line_of_sight_to: list = None,
        power_consumption_in_watt: float = None,
    ):
        """Registers an activity that can then be performed on the local actor.

        Args:
            name (str): Name of the activity
            requires_line_of_sight_to (list): List of strings with names of actors which need to be visible for this activity.
            power_consumption_in_watt (float, optional): Power consumption of performing
            the activity (per second). Defaults to None.
        """
        if name in self._activities.keys():
            raise ValueError(
                "Trying to add already existing activity with name: "
                + name
                + ". Already have "
                + str(self._activities[name])
            )

        self._activities[name] = DotMap(
            requires_line_of_sight_to=requires_line_of_sight_to,
            power_consumption_in_watt=power_consumption_in_watt,
            _dynamic=False,
        )

        logger.debug(f"Registered activity {self._activities[name]}")

    def perform_activity(
        self,
        name: str,
        local_actor: BaseActor,
        power_consumption_in_watt: float = None,
        duration_in_s: float = 1.0,
    ):
        """Perform the activity and discharge battery accordingly

        Args:
            name (str): Name of the activity
            local_actor (BaseActor): The local actor that is performing the activity.
            power_consumption_in_watt (float, optional): Power consumption of the
            activity in seconds if not specified. Defaults to None.
            duration_in_s (float, optional): Time to perform this activity. Defaults to 1.0.

        Returns:
            bool: Whether the activity was performed successfully.
        """
        # Check if activity exists and if it already had consumption specified
        assert name in self._activities.keys(), (
            "Activity not found. Declared activities are" + self._activities.keys()
        )
        activity = self._activities[name]
        logger.debug(f"Performing activity {activity}")

        if power_consumption_in_watt is None:
            power_consumption_in_watt = activity.power_consumption_in_watt

        assert power_consumption_in_watt > 0, (
            "Power consumption has to be positive but was either in activity or call specified as "
            + str(power_consumption_in_watt)
        )

        assert duration_in_s > 0, "Duration has to be positive."

        # TODO
        # Check if line of sight requirement is fulfilled and if enough power available
        assert (
            activity.requires_line_of_sight_to is None
        ), "Line of Sight for activities is not implemented"

        # TODO
        # Perform activity, maybe we allow the user pass a function to be executed?

        # Discharge power for the activity
        local_actor.discharge(power_consumption_in_watt, duration_in_s)

        logger.trace(f"Activity {activity} completed.")

        return True
