import logging


def set_logger(new_logger):
    global logger
    logger = new_logger


def disable_logger():
    logger.setLevel(logging.WARNING)


def enable_logger(level=logging.DEBUG):
    logger.setLevel(level)


logger = logging.getLogger("pyosexec")
logger.setLevel(logging.DEBUG)
