import types
import asyncio

from loguru import logger
from dotmap import DotMap

from paseos.actors.base_actor import BaseActor
from paseos.activities.activity_processor import ActivityProcessor


class ActivityManager:
    """This class is used to handle registering, performing and collection of activities.
    There can only be one instance of it and each paseos instance has one."""

    def __new__(self, paseos_instance, paseos_update_interval: float):
        if not hasattr(self, "instance"):
            self.instance = super(ActivityManager, self).__new__(self)
        else:
            logger.debug(
                "Tried to create another instance of ActivityManager. Keeping original one..."
            )
        return self.instance

    def __init__(self, paseos_instance, paseos_update_interval: float):
        """Creates a new activity manager. Singleton, so only one instance allowed.

        Args:
            paseos_instance (PASEOS): The main paseos instance.
            paseos_update_interval (float): Update interval for paseos.
        """
        logger.trace("Initializing ActivityManager")
        assert (
            paseos_update_interval > 1e-4
        ), f"Too small paseos update interval. Should not be less than 1e-4, was {paseos_update_interval}"
        self._activities = DotMap(_dynamic=False)
        self._paseos_update_interval = paseos_update_interval
        self._paseos_instance = paseos_instance

    def register_activity(
        self,
        name: str,
        activity_function: types.FunctionType,
        power_consumption_in_watt: float,
        check_termination_function: types.FunctionType,
        constraint_function: types.FunctionType,
    ):
        """Registers an activity that can then be performed on the local actor.

        Args:
            name (str): Name of the activity
            requires_line_of_sight_to (list): List of strings with names of actors which
            need to be visible for this activity.
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
            activity_function=activity_function,
            power_consumption_in_watt=power_consumption_in_watt,
            check_termination_function=check_termination_function,
            constraint_function=constraint_function,
            _dynamic=False,
        )

        logger.debug(f"Registered activity {self._activities[name]}")

    def perform_activity(
        self,
        name: str,
        local_actor: BaseActor,
        activity_func_args: list = None,
        termination_func_args: list = None,
        constraint_func_args: list = None,
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

        assert (
            activity.power_consumption_in_watt > 0
        ), "Power consumption has to be positive but was specified as " + str(
            activity.power_consumption_in_watt
        )

        processor = ActivityProcessor(
            update_interval=self._paseos_update_interval,
            power_consumption_in_watt=activity.power_consumption_in_watt,
            paseos_instance=self._paseos_instance,
            advance_paseos_clock=self._paseos_instance.use_automatic_clock,
        )

        # Define async functions to run the activity and processor
        async def run_activity(activity, args):
            await activity(args)
            await processor.stop()

        async def job():
            await asyncio.gather(
                processor.start(),
                run_activity(activity.activity_function, activity_func_args),
            )

        # Run activity and processor
        asyncio.run(job())

        logger.debug(f"Activity {activity} completed.")

        return True
