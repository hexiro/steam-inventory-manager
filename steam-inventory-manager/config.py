import pathlib
from dataclasses import dataclass

import yaml

from .classes import Account
from .types import Type


# for now im leaving these here instead of in "types.py"
# i might change my mind

@dataclass
class Options:
    min_price: float
    always_trade_graffities: bool = False
    always_trade_stickers: bool = False
    always_trade_agents: bool = False
    always_trade_containers: bool = False
    always_trade_collectibles: bool = False
    always_trade_patches: bool = False


config_file = pathlib.Path(__file__).parents[1] / "config.yaml"
config = yaml.safe_load(config_file.read_text(encoding="utf-8"))

main_account = Account(
    username=config["main-account"]["username"],
    password=config["main-account"]["password"],
    shared_secret=config["main-account"]["shared-secret"],
    identity_secret=config["main-account"]["identity-secret"]
)
alternate_accounts = [Account(
    username=acc["username"],
    password=acc["password"],
    shared_secret=acc["shared-secret"],
    identity_secret=acc["identity-secret"],
    priority=[Type(p.title() if p != "SMG" else p) for p in acc["priority"]] if "priority" in acc else None
) for acc in config["alternate-accounts"]]

options = Options(
    min_price=config["options"]["min-price"],
    always_trade_graffities=config["options"].get("always-trade-graffities", False),
    always_trade_stickers=config["options"].get("always-trade-stickers", False),
    always_trade_agents=config["options"].get("always-trade-agents", False),
    always_trade_containers=config["options"].get("always-trade-containers", False),
    always_trade_collectibles=config["options"].get("always-trade-collectibles", False),
    always_trade_patches=config["options"].get("always-trade-patches", False),
)
