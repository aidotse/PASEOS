from loguru import logger
from dotmap import DotMap
import pykep as pk

from .utils.load_default_cfg import load_default_cfg
from .utils.check_cfg import check_cfg
from .paseos import PASEOS
from .actors.base_actor import BaseActor
from .actors.actor_builder import ActorBuilder
from .actors.ground_station_actor import GroundstationActor
from .actors.spacecraft_actor import SpacecraftActor
from .central_body.central_body import CentralBody
from .communication.get_communication_window import get_communication_window
from .communication.find_next_window import find_next_window
from .power.power_device_type import PowerDeviceType
from .utils.reference_frame import ReferenceFrame
from .utils.set_log_level import set_log_level
from .visualization.plot import plot, PlotType


set_log_level("WARNING")

logger.debug("Loaded module.")


def init_sim(
    local_actor: BaseActor, cfg: DotMap = None, starting_epoch: pk.epoch = None
):
    """Initializes PASEOS

    Args:
        local_actor (BaseActor): The actor linked to the local device which is required to model anything.
        cfg (DotMap, optional): Configuration file. If None, default configuration will be used. Defaults to None.
        starting_epoch(pk.epoch): Starting epoch of the simulation. Will override cfg and local actor one.
    Returns:
        PASEOS: Instance of the simulation (only one can exist, singleton)
    """
    logger.debug("Initializing simulation.")
    if cfg is None:
        cfg = load_default_cfg()
        # If no start was specified neither via cfg or directly we use local actor time
        if starting_epoch is None:
            cfg.sim.start_time = local_actor.local_time.mjd2000 * pk.DAY2SEC
    else:
        check_cfg(cfg)

    if starting_epoch is not None:
        cfg.sim.start_time = starting_epoch.mjd2000 * pk.DAY2SEC

    if local_actor.local_time.mjd2000 * pk.DAY2SEC != cfg.sim.start_time:
        logger.warning(
            "You provided a different starting epoch for PASEOS than the local time of the local actor."
            + "starting_epoch will be used."
        )

    sim = PASEOS(local_actor=local_actor, cfg=cfg)
    return sim


__all__ = [
    "ActorBuilder",
    "BaseActor",
    "CentralBody",
    "find_next_window",
    "get_communication_window",
    "GroundstationActor",
    "load_default_cfg",
    "PASEOS",
    "plot",
    "PlotType",
    "PowerDeviceType",
    "ReferenceFrame",
    "set_log_level",
    "SpacecraftActor",
]
