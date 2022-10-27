import asyncio
from contextlib import suppress
from timeit import default_timer as timer

from loguru import logger


class ActivityProcessor:
    def __init__(
        self,
        update_interval: float,
        power_consumption_in_watt: float,
        paseos_instance,
        advance_paseos_clock=True,
    ):
        logger.trace("Initalized ActivityProcessor.")
        assert update_interval > 0, "Update update_interval has to be positive."
        assert (
            power_consumption_in_watt > 0
        ), "Power consumption has to be positive but was specified as " + str(
            power_consumption_in_watt
        )

        self._power_consumption_in_watt = power_consumption_in_watt
        self.update_interval = update_interval
        self.is_started = False
        self._task = None
        self._paseos_instance = paseos_instance
        self._advance_paseos_clock = advance_paseos_clock

    async def start(self):
        if not self.is_started:
            logger.trace("Starting ActivityProcessor.")
            # Remember when we start
            self.start_time = timer()
            self.is_started = True
            # Start task to call func periodically:
            self._task = asyncio.ensure_future(self._run())

    async def stop(self):
        if self.is_started:
            logger.trace("Stopping ActivityProcessor.")
            # Calculate elapsed time since last update
            elapsed_time = timer() - self.start_time
            # Perform final update
            await self._update(elapsed_time)
            self.is_started = False
            # Stop task and await it stopped:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def _update(self, elapsed_time):
        logger.debug("Running ActivityProcessor update.")

        logger.debug(f"Time since last update: {elapsed_time}s")
        if self._advance_paseos_clock:
            self._paseos_instance.advance_time(elapsed_time)

        self._paseos_instance.local_actor.discharge(
            self._power_consumption_in_watt, elapsed_time
        )

    async def _run(self):
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
