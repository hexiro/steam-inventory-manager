from functools import cached_property
from typing import List

import requests
from steam.steamid import SteamID

from ..types import Exterior, Item, Type


class Inventory:

    def __init__(self, steam_id: SteamID) -> None:
        self.steam_id = steam_id

    @cached_property
    def inventory(self) -> List[Item]:
        resp = requests.get(f"https://steamcommunity.com/inventory/{self.steam_id.as_64}/730/2?l=english&count=5000").json()
        assets: dict = resp["assets"]
        descriptions: dict = resp["descriptions"]

        items: List[Item] = []

        for item in descriptions:
            # this means that the item isn't currently tradable.
            # sometimes the item will never be tradable and other times it will be tradable after 7 days.
            if item["tradable"] == 0:
                continue
            classid = item["classid"]
            asset = next((x for x in assets if x["classid"] == classid), None)
            if not asset:
                continue

            type_values = [x.value for x in Type]
            # there may be better ways to parse this.
            raw_exterior = next((x["value"].split("Exterior: ")[-1] for x in item["descriptions"] if x["value"].startswith("Exterior: ")), None)
            raw_type = next((x["localized_tag_name"] for x in item["tags"] if x["category"] == "Type"), None)

            name = item["name"]
            # right now, only csgo is supported so these are hard coded
            appid = 730
            contextid = "2"
            amount = int(asset["amount"])
            assetid = asset["assetid"]
            # optionals
            exterior = Exterior(raw_exterior) if raw_exterior else None
            type = Type(raw_type) if raw_type and raw_type in type_values else None

            items.append(Item(
                name=name,
                appid=appid,
                contextid=contextid,
                amount=amount,
                assetid=assetid,
                exterior=exterior,
                type=type
            ))

        return items

    @property
    def items_to_trade(self):
        return [item for item in self.inventory if item.should_be_traded]


if __name__ == "__main__":
    print(Inventory(SteamID(76561199033382814)).inventory)
