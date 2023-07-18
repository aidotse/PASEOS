from enum import Enum


class ReferenceFrame(Enum):
    """Enum for used reference frames."""

    # CentralBodyInertial Reference Frame (i.e. non-rotating)
    CentralBodyInertial = 1
    # Heliocentric Reference Frame (i.e. Sun Centered Inertial, non-rotating)
    Heliocentric = 2
