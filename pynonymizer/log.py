import logging
import os
import sys

def get_default_logger():
    """
    Get the default logging instance
    :return:
    """
    return logging.getLogger("pynonymizer")


def get_logger(name):
    """
    Get a child logger of the default logger
    :param name: expects an arbitrary name or list of names to form into heirarchy
    :return:
    """

    if isinstance(name, str):
        child_logger_name = name
    else:
        child_logger_name = ".".join(name)

    if len(child_logger_name) < 1:
        raise ValueError("No logger name given.")

    return logging.getLogger(f"pynonymizer.{child_logger_name}")


def init_logging():
    # init default logger
    default_logger = get_default_logger()

    default_logger.setLevel(logging.DEBUG)
    default_file_formatter = logging.Formatter('[%(asctime)-15s|%(levelname)s|%(name)s] %(message)s')
    default_console_formatter = logging.Formatter('%(message)s')

    # Add default warn handler to console
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(default_console_formatter)
    default_logger.addHandler(console_handler)

init_logging()
