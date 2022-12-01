from loguru import logger
import pykep as pk
import numpy as np
from skyfield.api import load

from paseos.actors.base_actor import BaseActor


class GroundstationActor(BaseActor):
    """This class models a groundstation actor."""

    # Ground station latitude / longitude
    _skyfield_position = None

    # Timescale object to convert from pykep epoch to skyfield time
    _skyfield_timescale = load.timescale()

    def __init__(
        self,
        name: str,
        epoch: pk.epoch,
    ) -> None:
        """Constructor for a groundstation actor.

        Args:
            name (str): Name of this actor
            epoch (pykep.epoch): Epoch at this pos / velocity
        """
        logger.trace("Instantiating GroundstationActor.")
        super().__init__(name, epoch)

    def get_position(self, epoch: pk.epoch):
        """Compute the position of this ground station at a specific time.

        Args:
            epoch (pk.epoch): Time as pykep epoch

        Returns:
            np.array: [x,y,z] in meters
        """
        # Converting time to skyfield to use its API
        t_skyfield = self._skyfield_timescale.tt_jd(epoch.jd)

        # Getting ground station position, skyfield operates in GCRF frame
        # which is technically more precise than the J2000 we use but we neglect this here
        gcrf_position = self._skyfield_position.at(t_skyfield).position.m

        return gcrf_position
