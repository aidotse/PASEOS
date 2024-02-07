from abc import ABC, abstractmethod
from paseos.paseos import PASEOS


class Animation(ABC):
    """Abstract class for visualization."""

    def __init__(self, sim: PASEOS) -> None:
        """Initialize the animation

        Args:
            sim (PASEOS): simulation object
        """
        self._local_actor = sim.local_actor
        self._other_actors = sim.known_actors
        self.objects = list()

    def _sec_to_ddhhmmss(self, time: float) -> str:
        """Convert seconds to ddhhmmss format

        Args:
            time (float): time in seconds

        Returns:
            str: time in ddhhmmss.
        """
        m, s = divmod(time, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        return f"T={d:.0f}d{h:.0f}h{m:.0f}m{s:.0f}s"

    @abstractmethod
    def _plot_actors(self) -> None:
        """Function to plot all the actors"""
        pass

    @abstractmethod
    def update(self, sim: PASEOS) -> None:
        """Function to update all the objects in the animation

        Args:
            sim (PASEOS): simulation object
        """
        pass
