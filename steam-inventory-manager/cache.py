from __future__ import annotations

import base64
import json
import logging
import pathlib
import sys
import uuid
from typing import TYPE_CHECKING

from cryptography.fernet import Fernet, InvalidToken

if TYPE_CHECKING:
    from .datatypes import SessionData

logger = logging.getLogger(__name__)

# isn't perfect or trying to be perfect.
# If it changes it'll just make a new session and overwrite the file.
hardware_id = str(uuid.uuid1(uuid.getnode(), 0))[24:]
thirty_two = (hardware_id * 3)[:-4]
fernet = Fernet(base64.b64encode(thirty_two.encode()))


def cache_file(account_name: str) -> pathlib.Path | None:
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

    directory = appdata_equivalent / "steam-inventory-manager"
    directory.mkdir(exist_ok=True)
    return directory / account_name


def session_data(account_name: str) -> SessionData | None:
    file = cache_file(account_name)
    if not file or not file.exists():
        logger.debug("No cached data found.")
        return
    try:
        with open(file, "rb") as file:
            encrypted = file.read()

        decrypted = fernet.decrypt(encrypted).decode()
        deserialized = json.loads(decrypted)

        logger.debug("Reading cache file:")
        logger.debug(f"{deserialized=}")
        return deserialized
    except (json.JSONDecodeError, FileNotFoundError, InvalidToken):
        logger.debug("Failed to read from cache file.")
        return


def store_session_data(account_name: str, data: SessionData) -> None:
    file = cache_file(account_name)
    if not file:
        return
    logger.debug("Writing to cache file:")
    logger.debug(f"{data=}")
    logger.debug(f"{file=}")

    with open(file, "wb") as file:
        serialized = json.dumps(data)
        encrypted = fernet.encrypt(serialized.encode())
        file.write(encrypted)
