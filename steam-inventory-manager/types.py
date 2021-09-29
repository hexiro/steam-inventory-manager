from dataclasses import dataclass
from enum import Enum
from functools import cached_property

from .utils import PRICES
from . import config


class Exterior(Enum):
    FACTORY_NEW = "Factory New"
    MINIMAL_WEAR = "Minimal Wear"
    FIELD_TESTED = "Field-Tested"
    WELL_WORN = "Well-Worn"
    BATTLE_SCARRED = "Battle-Scarred"


@dataclass
class Item:
    # details about the item itself
    name: str
    is_weapon: bool
    # details about the item regarding to your inventory
    # most of these could be strings or integers, so im going off of what steam requires for their trading api
    appid: int
    contextid: str
    amount: int
    assetid: int
    # not required
    exterior: Exterior = None

    @property
    def market_name(self):
        return f"{self.name} {self.exterior.value}" if self.exterior else self.name

    @property
    def trade_asset(self):
        """ Contains all the details needed to trade an item """
        return {"appid": self.appid,
                "contextid": self.contextid,
                "amount": self.amount,
                "assetid": self.assetid}

    @cached_property
    def price(self) -> float:
        if self.market_name not in PRICES:
            return -1
        item = PRICES[self.market_name]
        if "price" not in item:
            return -1
        queue = ("30_days", "all_time", "7_days", "24_hours")
        # imo median is better then an average because of extreme
        # undercuts and super high prices skewing the average
        for key in queue:
            if key in item["prices"]:
                return item["prices"][key]["median"]
        return -1

    @property
    def should_be_traded(self):
        # if the item doesn't have a price, that generally means it's unpopular so for now i'll trade them.
        return self.price == -1 or self.price < config.options.min_price
