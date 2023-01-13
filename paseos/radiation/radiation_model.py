import numpy as np


class RadiationModel:
    """This class defines a simple radiation model for data corruption, random restarts and device failure due to radiation."""

    def __init__(
        self, data_corruption_events_per_s, restart_events_per_s, failure_events_per_s
    ) -> None:
        """Initializes the model.

        Args:
            data_corruption_events_per_s (float): Single bit of data being corrupted, events per second.
            restart_events_per_s (float): Device restart being triggered, events per second.
            failure_events_per_s (float): Complete device failure, events per second.
        """
        assert (
            data_corruption_events_per_s >= 0
        ), "data_corruption_events_per_s cannot be negative."
        assert restart_events_per_s >= 0, "restart_events_per_s cannot be negative."
        assert failure_events_per_s >= 0, "failure_events_per_s cannot be negative."

        self._data_corruption_events_per_s = data_corruption_events_per_s
        self._restart_events_per_s = restart_events_per_s
        self._failure_events_per_s = failure_events_per_s

    @staticmethod
    def _compute_poisson_nonzero_event_probability(events_per_s, interval_in_s):
        """Compute the probability of a poisson distributed event happening at least once.

        Args:
            events_per_s (float): How many events happen per second (poisson lamba)
            interval_in_s (float): How long the monitored interval is

        Returns:
            float: Probability of nonzero events.
        """
        return 1 - np.exp(-interval_in_s * events_per_s)

    @staticmethod
    def _sample_poisson_process(events_per_s, interval_in_s):
        """Sample a poisson process.

        Args:
            events_per_s (float): How many events happen per second (poisson lamba)
            interval_in_s (float): How long the monitored interval is

        Returns:
            bool: Whether event happened at least ones
        """
        poisson_prob = RadiationModel._compute_poisson_nonzero_event_probability(
            events_per_s, interval_in_s
        )
        return np.random.rand() > poisson_prob

    def model_data_corruption(self, data, exposure_period_in_s: float):
        pass

    def did_device_restart(self, interval_in_s: float):
        """Models whether the device experienced a random restart in this interval.

        Args:
            interval_in_s (float): Time interval length in seconds.

        Returns:
            bool: Whether restart event occured.
        """
        assert interval_in_s > 0, "Time interval must be positive."
        return RadiationModel._sample_poisson_process(
            self._restart_events_per_s, interval_in_s
        )

    def did_device_experience_failure(self, interval_in_s: float):
        """Models whether the device experienced a failure in this interval.

        Args:
            interval_in_s (float): Time interval length in seconds.

        Returns:
            bool: Whether restart event occured.
        """
        assert interval_in_s > 0, "Time interval must be positive."
        return RadiationModel._sample_poisson_process(
            self._failure_events_per_s, interval_in_s
        )
