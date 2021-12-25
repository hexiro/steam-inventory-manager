from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

import yaml

from .exceptions import ConfigurationError

if TYPE_CHECKING:
    from .datatypes import ConfigurationAccount, ConfigurationOptions

try:
    config_file = pathlib.Path(__file__).parents[1] / "config.yaml"
    config = yaml.safe_load(config_file.read_text(encoding="utf-8"))
except yaml.YAMLError:
    raise ConfigurationError("failed to load config.yaml")

try:
    main_account: ConfigurationAccount = config["main-account"]
    alternate_accounts: list[ConfigurationAccount] = config["alternate-accounts"]
    options: ConfigurationOptions = config["options"]
except KeyError as e:
    raise ConfigurationError(f"key, {e} not present in config.yaml") from None
