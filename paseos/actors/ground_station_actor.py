from loguru import logger
import pykep as pk

from paseos.actors.base_actor import BaseActor


class GroundstationActor(BaseActor):
    """This class models a groundstation actor."""

    def __init__(
        self, name: str, position, velocity, epoch: pk.epoch, central_body: pk.planet
    ) -> None:
        """Constructor for a groundstation actor.
        Pos / velocity are relative to central body origin.

        Args:
            name (str): Name of this actor
            position (list of floats): [x,y,z]
            velocity (list of floats): [vx,vy,vz]
            epoch (pykep.epoch): Epoch at this pos / velocity
            central_body (pk.planet): pykep central body
        """
        logger.trace("Instantiating GroundstationActor.")
        super().__init__(name, position, velocity, epoch, central_body)
