from loguru import logger
import sys


def set_log_level(log_level: str):
    """Set the log level for the logger.

    Args:
        log_level (str): The log level to set. Options are 'TRACE','DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL'.
    """
    logger.remove()
    logger.add(
        sys.stderr,
        colorize=True,
        level=log_level.upper(),
        format="<green>{time:HH:mm:ss}</green>|PASEOS-<blue>{level}</blue>| <level>{message}</level>",
        filter="paseos",
    )
    logger.debug(f"Setting LogLevel to {log_level.upper()}")
