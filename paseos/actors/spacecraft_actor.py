from loguru import logger

from paseos.actors.base_actor import BaseActor


class SpacecraftActor(BaseActor):
    """This class models a spacecraft actor which in addition to pos,velocity also has additional constraints such as power/battery."""

    # Power constraints
    # TODO
    _available_power = None

    def __init__(self) -> None:
        logger.trace("Instantiating SpacecraftActor.")
        super().__init__()
