from loguru import logger
import pykep as pk

from paseos.actors.base_actor import BaseActor


class SpacecraftActor(BaseActor):
    """This class models a spacecraft actor which in addition to pos,velocity also has additional constraints such as power/battery."""

    # Power constraints
    # TODO
    _available_power = None

    def __init__(
        self, name: str, position, velocity, epoch: pk.epoch, central_body: pk.planet
    ) -> None:
        """Constructor for a spacecraft actor

        Args:
            name (str): Name of this actor
            position (list of floats): [x,y,z]
            velocity (list of floats): [vx,vy,vz]
            epoch (pykep.epoch): Epoch at this pos / velocity
            central_body (pk.planet): pykep central body
        """
        logger.trace("Instantiating SpacecraftActor.")
        super().__init__(name, position, velocity, epoch, central_body)
