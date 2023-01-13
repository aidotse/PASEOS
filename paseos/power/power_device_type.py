from enum import Enum


class PowerDeviceType(Enum):
    """Describes the different power device types
    1 - Solar Panels
    2 - Radioisotope Thermoelectric Generator (RTG)
    """

    SolarPanel = 1
    RTG = 2
