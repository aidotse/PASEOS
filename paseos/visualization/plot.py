from enum import Enum

from ..paseos import PASEOS
from .space_animation import SpaceAnimation


class PlotType(Enum):
    """Describes the different plot types
    1 - SpacePlot
    """

    SpacePlot = 1


def plot(sim: PASEOS, plot_type: PlotType, filename: str = None):
    """Creates the animation object

    Args:
        sim (PASEOS): simulation object
        plot_type (PlotType): enum deciding what kind of plot object to be made
        filename (str, optional): filename to save the animation to. Defaults to None.

    Raises:
        ValueError: supplied plot type not supported

    Returns:
        Animation: Animation object
    """
    if plot_type is PlotType.SpacePlot:
        return SpaceAnimation(sim, filename=filename)
    else:
        raise ValueError(f"PlotType {plot_type} not known. Available are {[e for e in PlotType]}")
