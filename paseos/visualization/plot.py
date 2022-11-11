from enum import Enum
from loguru import logger

from ..paseos import PASEOS
from .space_animation import SpaceAnimation


class PlotType(Enum):
    """Describes the different plot types
    1 - SpacePlot
    """

    SpacePlot = 1


def plot(sim: PASEOS, plot_type: PlotType):
    if plot_type is PlotType.SpacePlot:
        return SpaceAnimation(sim)
    else:
        raise ValueError(
            f"PlotType {plot_type} not known. Available are {[e for e in PlotType]}"
        )
