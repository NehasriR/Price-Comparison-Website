import logging

from colorama import Fore, Style, init
from colorlog import ColoredFormatter
import pyfiglet


def configure_logging():
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(white)s%(message)s",
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.handlers = []
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def display_banner():
    init(autoreset=True)
    ascii_banner = pyfiglet.figlet_format("SHOPSENSE", font="standard")
    colored_banner = (
        Fore.CYAN
        + ascii_banner
        + Fore.MAGENTA
        + "The Product Price Comparison Tool\n"
        + Style.RESET_ALL
    )
    print(colored_banner)
