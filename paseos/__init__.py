from loguru import logger

from paseos.actors.base_actor import BaseActor

from .utils.set_log_level import set_log_level
from .utils.load_default_cfg import load_default_cfg
from .paseos import PASEOS
from .visualization.plot import plot, PlotType
from .actors.actor_builder import ActorBuilder
from .actors.spacecraft_actor import SpacecraftActor
from .actors.ground_station_actor import GroundstationActor


set_log_level("DEBUG")

logger.debug("Loaded module.")


def init_sim(local_actor: BaseActor, cfg=None):
    """Initializes PASEOS

    Args:
        local_actor (BaseActor): The actor linked to the local device which is required to model anything.
        cfg (DotMap, optional): configuration file. If None, default configuration will be used. Defaults to None
    Returns:
        PASEOS: Instance of the simulation (only one can exist, singleton)
    """
    logger.debug("Initializing simulation.")
    if cfg is not None:
        cfg = cfg
    else:
        cfg = load_default_cfg()
    sim = PASEOS(local_actor=local_actor, cfg=cfg)
    return sim


__all__ = [
    "ActorBuilder",
    "GroundstationActor",
    "plot",
    "PlotType",
    "SpacecraftActor",
]
