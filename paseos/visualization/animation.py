from abc import ABC, abstractmethod
from paseos.paseos import PASEOS


class Animation(ABC):
    """Abstract class for visualization."""

    def __init__(self, sim: PASEOS) -> None:
        self._local_actor = sim.local_actor
        self._other_actors = sim.known_actors
        self.objects = list()

    def _sec_to_ddhhmmss(self, time: float) -> str:
        m, s = divmod(time, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        return f"T={d:.0f}d{h:.0f}h{m:.0f}m{s:.0f}s"

    @abstractmethod
    def _plot_actors(self) -> None:
        pass

    @abstractmethod
    def update(self, sim: PASEOS) -> None:
        pass
