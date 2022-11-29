from loguru import logger
import pykep as pk

from paseos.actors.base_actor import BaseActor


class GroundstationActor(BaseActor):
    """This class models a groundstation actor."""

    def __init__(self, name: str, epoch: pk.epoch) -> None:
        """Constructor for a groundstation actor.

        Args:
            name (str): Name of this actor
            epoch (pykep.epoch): Epoch at this pos / velocity
        """
        logger.trace("Instantiating GroundstationActor.")
        super().__init__(name, epoch)
