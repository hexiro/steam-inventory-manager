import json
import pathlib
import sys

# gets appdata folder cross-platform
# reference: https://doc.qt.io/qt-5/qstandardpaths.html
from typing import Optional


def cached_file(account_name: str) -> Optional[pathlib.Path]:
    """
    Returns a parent directory path
    where persistent application data can be stored.

    # linux: ~/.local/share
    # macOS: ~/Library/Application Support
    # windows: C:/Users/<USER>/AppData/Roaming
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
    folder.mkdir(exist_ok=True)

    return folder / (account_name + ".json")


def account_data(account_name: str) -> dict:
    file = cached_file(account_name)
    if not file or not file.exists():
        return {}
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def store_account_data(account_name: str, **kwargs):
    file = cached_file(account_name)
    if file:
        file.write_text(json.dumps(kwargs), encoding="utf-8")
