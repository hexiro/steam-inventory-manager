from __future__ import annotations

import logging
import sys
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL

import colorama
from colorama import Fore, Style


class ColoredFormatter(logging.Formatter):
    """
    Colors output based on level.

    References:
        https://stackoverflow.com/a/56944256
    """

    def __init__(self, fmt: str | None = None, datefmt: str | None = None) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.FORMATS: dict[int, logging.Formatter] = {
            DEBUG: logging.Formatter(Fore.YELLOW + fmt),
            INFO: logging.Formatter(fmt),
            WARNING: logging.Formatter(Fore.LIGHTYELLOW_EX + fmt),
            ERROR: logging.Formatter(Fore.RED + fmt),
            CRITICAL: logging.Formatter(Fore.RED + Style.BRIGHT + fmt),
        }

    def format(self, record: logging.LogRecord) -> str:
        formatter = self.FORMATS.get(record.levelno)
        return formatter.format(record)


def setup() -> None:
    colorama.init(autoreset=True)

    logging.root.setLevel(INFO)

    _stream_handler = logging.StreamHandler(stream=sys.stdout)
    _stream_handler.setFormatter(ColoredFormatter(fmt="[%(levelname)s]: %(message)s"))

    logging.root.addHandler(_stream_handler)
