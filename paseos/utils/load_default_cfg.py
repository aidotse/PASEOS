import os
import toml
from dotmap import DotMap
from loguru import logger


def load_default_cfg():
    """Loads the default toml config file from the cfg folder."""

    path = os.path.join(os.path.dirname(__file__) + "/../resources/", "default_cfg.toml")
    logger.debug(f"loading default cfg from path: {path}")

    with open(path) as cfg:
        # dynamic=False inhibits automatic generation of non-existing keys
        return DotMap(toml.load(cfg), _dynamic=False)
