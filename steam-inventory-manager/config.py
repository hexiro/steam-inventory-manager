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
    disallow_graffities: bool


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
    disallow_graffities=config["options"]["disallow-graffities"],
)
