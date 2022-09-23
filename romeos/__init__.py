from loguru import logger

from .utils.set_log_level import set_log_level
from .romeos import ROMEOS

set_log_level("DEBUG")

logger.debug("Loaded module.")


def init_sim():
    logger.debug("Initializing simulation.")
    sim = ROMEOS()
    sim.init()
    return sim


__all__ = ["init"]
