import pathlib
from dataclasses import dataclass
from enum import Enum
from typing import List

from .types import Type

import yaml


# for now im leaving these here instead of in "types.py"
# i might change my mind

@dataclass
class MainAccount:
    username: str
    password: str
    shared_secret: str
    identity_secret: str


@dataclass
class AlternateAccount:
    username: str
    password: str
    shared_secret: str
    identity_secret: str
    priority: List[Type] = None


@dataclass
class Options:
    min_price: float
    disallow_graffities: bool


config_file = pathlib.Path(__file__).parents[1] / "config.yaml"
config = yaml.safe_load(config_file.read_text(encoding="utf-8"))

main_account = MainAccount(
    username=config["main-account"]["username"],
    password=config["main-account"]["password"],
    shared_secret=config["main-account"]["shared-secret"],
    identity_secret=config["main-account"]["identity-secret"]
)
alternate_accounts = [AlternateAccount(
    username=acc["username"],
    password=acc["password"],
    shared_secret=acc["shared-secret"],
    identity_secret=acc["identity-secret"],
    priority=[Type(p.title()) for p in acc["priority"]] if "priority" in acc else None
) for acc in config["alternate-accounts"]]

options = Options(
    min_price=config["options"]["min-price"],
    disallow_graffities=config["options"]["disallow-graffities"],
)
