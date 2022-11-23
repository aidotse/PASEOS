import asyncio
from contextlib import suppress
import types

from loguru import logger


class ActivityRunner:
    """This class is used to run the activities specified by the user and encapsulates the logic for canceling them."""

    def __init__(
        self,
        name: str,
        activity_func: types.CoroutineType,
        constraint_func: types.CoroutineType = None,
        termination_func: types.CoroutineType = None,
        termination_args: list = None,
        constraint_args: list = None,
    ):
        """Creates a new runner for the activity. This takes of running it in interplay with the activity processor.

        Args:
            name (str): Name of the activity.
            activity_func (types.CoroutineType): Function to execute for the activity.
            constraint_func (types.CoroutineType, optional): Constraint function of the activity.
            See Activity Manager for more details. Defaults to None.
            termination_func (types.CoroutineType, optional): Termination function of the activity.
            See Activity Manager for more details. Defaults to None.
            termination_args (list, optional): Termination arguments of the activity. See Activity
            Manager for more details. Defaults to None.
            constraint_args (list, optional): Constraint arguments of the activity. See Activity
            Manager for more details. Defaults to None.
        """
        logger.trace(f"Initalized activity {name}")
        self.name = name
        self._activity_func = activity_func
        self._constraint_func = constraint_func
        self._termination_func = termination_func
        self._termination_args = termination_args
        self._constraint_args = constraint_args
        self._was_stopped = False

    def has_constraint(self):
        """Whether this activity has a constraint function specified.

        Returns:
            bool: True if specified.
        """
        return self._constraint_func is not None

    async def _run(self, args):
        try:
            await self._activity_func(args)
        except Exception as e:
            logger.error(f"An exception occurred running the activity {self.name}.")
            logger.error(str(e))

    async def start(self, args):
        """Start running the activity.

        Args:
            args (list): Arguments for the activity function.
        """
        logger.trace(f"Running activity {self.name}.")
        self._was_stopped = False
        self._task = asyncio.create_task(self._run(args))
        with suppress(asyncio.CancelledError):
            await self._task
        if not self._was_stopped:
            await self.stop()

    async def stop(self):
        """Stops the activity execution and calls the termination function."""

        logger.trace(f"Stopping activity {self.name}.")
        if self._termination_func is not None:
            logger.debug(f"Calling termination function of activity {self.name}")
            try:
                await self._termination_func(self._termination_args)
            except Exception as e:
                logger.error(
                    f"An exception occurred running the terminating the activity {self.name}."
                )
                logger.error(str(e))
        self.is_started = False
        # Stop task and await it stopped:
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._was_stopped = True

    async def check_constraint(self):
        """Checks whether the activities constraints are still valid.

        Returns:
            bool: True if still valid.
        """
        if self.has_constraint():
            logger.trace(f"Checking activity {self.name} constraints")
            try:
                is_satisfied = await self._constraint_func(self._constraint_args)
            except Exception as e:
                logger.error(
                    f"An exception occurred running the checking the activity's {self.name} constraint."
                )
                logger.error(str(e))
                return False
            if not is_satisfied or is_satisfied is None:
                logger.debug(
                    f"Constraint of activity {self.name} is no longer satisfied, cancelling."
                )
                if not self._was_stopped:
                    await self.stop()
                return False
        else:
            logger.warning(
                f"Checking activity {self.name} constraints even though activity has no constraints."
            )
        return True
