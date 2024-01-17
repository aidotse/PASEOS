from enum import Enum


class LinkType(Enum):
    """Describes the different link types
    1 - Satellite to ground radio (S2G)
    2 - Satellite to satellite optical (intersatellite link: ISL)
    """

    S2G = 1
    ISL = 2
