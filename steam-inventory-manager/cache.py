from __future__ import annotations

import json
import logging
import pathlib
import sys
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .datatypes import SessionData

logger = logging.getLogger(__name__)


def cache_file(account_name: str) -> Optional[pathlib.Path]:
    """
    Returns a parent directory path
    where persistent application data can be stored.

    # linux: ~/.local/share
    # macOS: ~/Library/Application Support
    # windows: C:/Users/<USER>/AppData/Roaming

    References:
        https://doc.qt.io/qt-5/qstandardpaths.html
    """
    home = pathlib.Path.home()

    if sys.platform == "win32":
        appdata_equivalent = home / "AppData/Roaming"
    elif sys.platform == "linux":
        appdata_equivalent = home / ".local/share"
    elif sys.platform == "darwin":
        appdata_equivalent = home / "Library/Application Support"
    else:
        return

    folder = appdata_equivalent / "steam-inventory-manager"
    try:
        folder.mkdir(exist_ok=True)
    except OSError:
        return

    return folder / (account_name + ".json")


def session_data(account_name: str) -> Optional[SessionData]:
    file = cache_file(account_name)
    if not file or not file.exists():
        logger.debug("No cached data found.")
        return
    try:
        with open(file, "r", encoding="utf-8", errors="ignore") as file:
            data = json.load(file)
        logger.debug("Reading cache file:")
        logger.debug(f"{data=}")
        return data
    except (json.JSONDecodeError, FileNotFoundError):
        logger.debug("Failed to read from cache file.")
        return


def store_session_data(account_name: str, data: SessionData) -> None:
    file = cache_file(account_name)
    if not file:
        return
    logger.debug("Writing to cache file:")
    logger.debug(f"{data=}")
    logger.debug(f"{file=}")
    with open(file, "w", encoding="utf-8", errors="ignore") as file:
        json.dump(data, file)
