import pathlib
from typing import List, TypedDict, Optional

import yaml

from .exceptions import ConfigurationError


# for config.py

ConfigurationAccount = TypedDict(
    "ConfigurationAccount",
    {"username": str, "password": str, "shared-secret": str, "identity-secret": str, "priorities": Optional[list[str]]},
)

ConfigurationOptions = TypedDict(
    "ConfigurationOptions",
    {
        "min-price": float,
        "always-trade-graffities": bool,
        "always-trade-stickers": bool,
        "always-trade-agents": bool,
        "always-trade-containers": bool,
        "always-trade-collectibles": bool,
        "always-trade-patches": bool,
    },
)


try:
    config_file = pathlib.Path(__file__).parents[1] / "config.yaml"
    config = yaml.safe_load(config_file.read_text(encoding="utf-8"))
except yaml.YAMLError:
    raise ConfigurationError("failed to load config.yaml")

try:
    main_account: ConfigurationAccount = config["main-account"]
    alternate_accounts: List[ConfigurationAccount] = config["alternate-accounts"]
    options: ConfigurationOptions = config["options"]
except KeyError as e:
    raise ConfigurationError(f"key, {e} not present in config.yaml") from None
