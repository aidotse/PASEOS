import types
import asyncio

from loguru import logger
from dotmap import DotMap

from paseos.activities.activity_processor import ActivityProcessor
from paseos.activities.activity_runner import ActivityRunner
from paseos.utils.is_notebook import is_notebook


class ActivityManager:
    """This class is used to handle registering, performing and collection of activities."""

    def __init__(
        self,
        paseos_instance,
        paseos_update_interval: float,
        paseos_time_multiplier: float,
    ):
        """Creates a new activity manager. Singleton, so only one instance allowed.

        Args:
            paseos_instance (PASEOS): The main paseos instance.
            paseos_update_interval (float): Update interval for paseos.
            paseos_time_multiplier (float): Multiplier for the time. At 1, it is real time.
        """
        logger.trace("Initializing ActivityManager")
        assert (
            paseos_update_interval > 1e-4
        ), f"Too small paseos update interval. Should not be less than 1e-4, was {paseos_update_interval}"
        assert (
            paseos_time_multiplier > 1e-4
        ), f"Too small paseos paseos_time_multiplier. Should not be less than 1e-4, was {paseos_time_multiplier}"
        self._activities = DotMap(_dynamic=False)
        self._paseos_update_interval = paseos_update_interval
        self._paseos_time_multiplier = paseos_time_multiplier
        self._paseos_instance = paseos_instance

    def remove_activity(self, name: str):
        """Removes a registered activity

        Args:
            name (str): Name of the activity.
        """
        if name not in self._activities.keys():
            raise ValueError(
                "Trying to remove non-existing activity with name: " + name
            )
        else:
            del self._activities[name]

    def register_activity(
        self,
        name: str,
        activity_function: types.CoroutineType,
        power_consumption_in_watt: float,
        on_termination_function: types.CoroutineType,
        constraint_function: types.CoroutineType,
    ):
        """Registers an activity that can then be performed on the local actor.

        Args:
            name (str): Name of the activity.
            activity_function (types.CoroutineType): Function to execute during the activity.
            Needs to be async. Can accept a list of arguments to be specified later.
            power_consumption_in_watt (float): Power consumption of the activity in W (per second).
            on_termination_function (types.CoroutineType): Function to execute when the activities
            stops (either due to completion or constraint not being satisfied anymore).
            Needs to be async. Can accept a list of arguments to be specified later.
            constraint_function (types.CoroutineType): Function to evaluate if constraints are still valid.
            Should return True if constraints are valid, False if they aren't. Needs to be async.
            Can accept a list of arguments to be specified later.
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
            on_termination_function=on_termination_function,
            constraint_function=constraint_function,
            _dynamic=False,
        )

        logger.debug(f"Registered activity {self._activities[name]}")

    def perform_activity(
        self,
        name: str,
        activity_func_args: list = None,
        termination_func_args: list = None,
        constraint_func_args: list = None,
    ):
        """Perform the specified activity. Will advance the simulation if automatic clock is not disabled.

        Args:
            name (str): Name of the activity to perform.
            activity_func_args (list, optional): Arguments for the activity function. Defaults to None.
            termination_func_args (list, optional): Arguments for the termination function. Defaults to None.
            constraint_func_args (list, optional): Arguments for the constraint function. Defaults to None.
        """
        # Check if activity exists and if it already had consumption specified
        assert (
            name in self._activities.keys()
        ), f"Activity not found. Declared activities are {self._activities.keys()}"
        activity = self._activities[name]
        logger.debug(f"Performing activity {activity}")

        assert (
            activity.power_consumption_in_watt >= 0
        ), "Power consumption has to be positive but was specified as " + str(
            activity.power_consumption_in_watt
        )

        activity_runner = ActivityRunner(
            name=name,
            activity_func=activity.activity_function,
            constraint_func=activity.constraint_function,
            termination_func=activity.on_termination_function,
            termination_args=termination_func_args,
            constraint_args=constraint_func_args,
        )

        async def job():
            processor = ActivityProcessor(
                update_interval=self._paseos_update_interval,
                power_consumption_in_watt=activity.power_consumption_in_watt,
                paseos_instance=self._paseos_instance,
                activity_runner=activity_runner,
                time_multiplier=self._paseos_time_multiplier,
                advance_paseos_clock=self._paseos_instance.use_automatic_clock,
            )

            await asyncio.wait(
                [
                    asyncio.create_task(processor.start()),
                    asyncio.create_task(activity_runner.start(activity_func_args)),
                ],
                return_when=asyncio.ALL_COMPLETED,
            )
            await asyncio.wait([asyncio.create_task(processor.stop())])
            self._paseos_instance._is_running_activity = False
            self._paseos_instance._local_actor._current_activity = None
            del processor

        # Workaround to avoid error when executed in a Jupyter notebook.
        self._paseos_instance._local_actor._current_activity = name
        if is_notebook():
            return job()
        else:
            # Run activity and processor
            asyncio.gather(job())

        logger.info(f"Activity {activity} completed.")
