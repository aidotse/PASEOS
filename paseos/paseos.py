from dotmap import DotMap
from loguru import logger

from .utils.load_default_cfg import load_default_cfg


class PASEOS:
    """This class serves as the main interface with the user. It is designed as a singleton to ensure we only have one instance running at any time."""

    # Config file of the simulation
    # Beyond the initial cfg we use it to store variables
    # like the central body etc.
    _cfg = None

    def __new__(self):
        if not hasattr(self, "instance"):
            self.instance = super(PASEOS, self).__new__(self)
        else:
            logger.warning(
                "Tried to create another instance of PASEOS simulation. Keeping original one..."
            )
        return self.instance

    def __init__(self):
        logger.trace("Initializing PASEOS")
        self._cfg = load_default_cfg()
        pass

    def get_cfg(self) -> DotMap:
        """Returns the current cfg of the simulation

        Returns:
            DotMap: cfg
        """
        return self._cfg
