from dataclasses import dataclass
from enum import Enum
from functools import cached_property

from . import config
from .utils import PRICES


class Exterior(Enum):
    FACTORY_NEW = "Factory New"
    MINIMAL_WEAR = "Minimal Wear"
    FIELD_TESTED = "Field-Tested"
    WELL_WORN = "Well-Worn"
    BATTLE_SCARRED = "Battle-Scarred"


class Type(Enum):
    # weapon types
    KNIFE = "Knife"
    GLOVES = "Gloves"
    PISTOL = "Pistol"
    RIFLE = "Rifle"
    SNIPER_RIFLE = "Sniper Rifle"
    SHOTGUN = "Shotgun"
    SMG = "SMG"
    MACHINEGUN = "Machinegun"
    # other
    GRAFFITI = "Graffiti"
    STICKER = "Sticker"
    AGENT = "Agent"
    CONTAINER = "Container"


@dataclass
class Item:
    # details about the item itself
    name: str
    # details about the item regarding to your inventory
    # most of these could be strings or integers, so im going off of what steam requires for their trading api
    appid: int
    contextid: str
    amount: int
    assetid: int
    # not required
    exterior: Exterior = None
    type: Type = None

    @property
    def is_weapon(self):
        # do gloves count as a weapon? probably not. but are they a *weapon* skin? yes
        return Type in {Type.KNIFE, Type.GLOVES, Type.PISTOL, Type.RIFLE, Type.SNIPER_RIFLE, Type.SHOTGUN, Type.SMG, Type.MACHINEGUN}

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
