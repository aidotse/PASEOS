from enum import Enum


class DeviceType(Enum):
    """Describes the different communication device types
    1 - A radio transmitter
    2 - A radio receiver
    3 - An optical transmitter
    4 - An optical receiver
    """

    RADIO_TRANSMITTER = 1
    RADIO_RECEIVER = 2
    OPTICAL_TRANSMITTER = 3
    OPTICAL_RECEIVER = 4
