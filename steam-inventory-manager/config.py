import pathlib

import yaml

from .classes import Account
from .datatypes import ItemType, ConfigurationOptions
from .exceptions import ConfigurationError

try:
    config_file = pathlib.Path(__file__).parents[1] / "config.yaml"
    config = yaml.safe_load(config_file.read_text(encoding="utf-8"))
except yaml.YAMLError:
    raise ConfigurationError("failed to load config.yaml")

try:
    main_account = Account(
        username=config["main-account"]["username"],
        password=config["main-account"]["password"],
        shared_secret=config["main-account"]["shared-secret"],
        identity_secret=config["main-account"]["identity-secret"],
    )
    alternate_accounts = [
        Account(
            username=acc["username"],
            password=acc["password"],
            shared_secret=acc["shared-secret"],
            priorities=[ItemType(p.title() if p != "SMG" else p) for p in acc["priorities"]]
            if "priorities" in acc
            else None,
        )
        for acc in config["alternate-accounts"]
    ]

    options = ConfigurationOptions(
        min_price=config["options"]["min-price"],
        always_trade_graffities=config["options"].get("always-trade-graffities", False),
        always_trade_stickers=config["options"].get("always-trade-stickers", False),
        always_trade_agents=config["options"].get("always-trade-agents", False),
        always_trade_containers=config["options"].get("always-trade-containers", False),
        always_trade_collectibles=config["options"].get("always-trade-collectibles", False),
        always_trade_patches=config["options"].get("always-trade-patches", False),
    )
except KeyError as e:
    raise ConfigurationError(f"key, {e} not present in config.yaml") from None
