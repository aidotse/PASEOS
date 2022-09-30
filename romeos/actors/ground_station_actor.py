from loguru import logger

from romeos.actors.base_actor import BaseActor


class GroundstationActor(BaseActor):
    """This class models a groundstation actor."""

    def __init__(self) -> None:
        logger.trace("Instantiating GroundstationActor.")
        super().__init__()
