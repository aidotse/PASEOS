from dotmap import DotMap
from loguru import logger

from .utils.load_default_cfg import load_default_cfg


class ROMEOS:
    """This class serves as the main interface with the user. It is designed as a singleton to ensure we only have one instance running at any time."""

    _cfg = None

    def __new__(self):
        if not hasattr(self, "instance"):
            self.instance = super(ROMEOS, self).__new__(self)
        else:
            logger.warning("Tried to create another instance of ROMEOS simulation.")
        return self.instance

    def init(self):
        logger.trace("Initializing ROMEOS")
        self._cfg = load_default_cfg()
        pass

    def get_cfg(self) -> DotMap:
        return self._cfg
