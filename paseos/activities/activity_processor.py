import asyncio
from contextlib import suppress
from timeit import default_timer as timer

from loguru import logger

from paseos.activities.activity_runner import ActivityRunner


class ActivityProcessor:
    """This class specifies the processor of paseos running in the background during an activity."""

    def __init__(
        self,
        update_interval: float,
        power_consumption_in_watt: float,
        paseos_instance,
        activity_runner: ActivityRunner,
        time_multiplier: float = 1,
    ):
        """Initializes the ActivityProcessor.

        Args:
            update_interval (float): Interval at which we process (in s)
            power_consumption_in_watt (float): Power consumption of the activity. Used to discharge local actor.
            paseos_instance (PASEOS): Local paseos instance.
            activity_runner (ActivityRunner): Runner of the activity that is performed.
            Needed check if constraints are still valid.
            time_multiplier (float): Specifies the rate at which times passes to allow faster-than-real time modeling.
            the actor and thus local simulation. Defaults to True.
        """
        logger.trace("Initalized ActivityProcessor.")
        assert update_interval > 0, "Update update_interval has to be positive."
        assert (
            power_consumption_in_watt >= 0
        ), "Power consumption has to be positive but was specified as " + str(
            power_consumption_in_watt
        )

        self._power_consumption_in_watt = power_consumption_in_watt
        assert update_interval > 0, "update_interval has to be > 0"
        self.update_interval = update_interval
        assert time_multiplier > 1e-4, "time_multiplier has to be > 1e-4"
        self._time_multiplier = time_multiplier
        self._is_started = False
        self._task = None
        self._paseos_instance = paseos_instance
        self._activity_runner = activity_runner

    async def start(self):
        """Starts the processor."""
        if not self._is_started:
            logger.trace("Starting ActivityProcessor.")
            # Remember when we start
            self.start_time = timer()
            self._is_started = True
            # Start task to call func periodically:
            self._task = asyncio.create_task(self._run())

    async def stop(self):
        """Stops the processor."""
        if self._is_started:
            logger.trace("Stopping ActivityProcessor.")
            # Calculate elapsed time since last update
            elapsed_time = timer() - self.start_time
            # Perform final update if not interrupted before (otherwise already upto date)
            if (
                not self._paseos_instance.local_actor.was_interrupted
                and not self._paseos_instance.local_actor.is_dead
            ):
                await self._update(elapsed_time)
            # Reset interrupt (to prepare for potential next interrupt)
            self._paseos_instance.local_actor._was_interrupted = False
            self._is_started = False
            # Stop task and await it stopped:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            logger.trace("Processor stopped.")

    async def _update(self, elapsed_time: float):
        """Updates the processor and optionally local actor.

        Args:
            elapsed_time (float): Elapsed time in seconds.
        """
        assert elapsed_time > 0, "Elapsed time cannot be negative."
        logger.debug("Running ActivityProcessor update.")
        logger.debug(f"Time since last update: {elapsed_time}s")
        logger.trace(f"Applying time multiplier of {self._time_multiplier}")
        elapsed_time *= self._time_multiplier
        self._paseos_instance.advance_time(
            elapsed_time, self._power_consumption_in_watt
        )

    async def _run(self):
        """Main processor loop. Will track time, update paseos and check constraints of the activity."""
        while True:
            # Calculate elapsed time since last update
            elapsed_time = timer() - self.start_time

            # Make sure we don't update more frequently than specified
            # by waiting till we at least update_interval time elapsed.
            if elapsed_time < self.update_interval:
                await asyncio.sleep(self.update_interval - elapsed_time)
                elapsed_time = timer() - self.start_time

            # Start new timer
            self.start_time = timer()

            # Perform the update
            await self._update(elapsed_time)

            # Check if the activity should still run
            # otherwise stop it and then the processor

            # Radiation interruption leads to stop
            if (
                self._paseos_instance.local_actor.was_interrupted
                or self._paseos_instance.local_actor.is_dead
            ):
                await self.stop()
                await self._activity_runner.stop()

            if self._activity_runner.has_constraint():
                if not await self._activity_runner.check_constraint():
                    await self.stop()
