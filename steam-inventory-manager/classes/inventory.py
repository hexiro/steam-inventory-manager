from functools import cached_property
from typing import Union, List

import requests
from steam.steamid import SteamID

from ..types import Exterior, Item


# TODO: maybe an `item` dataclass?
# TODO: finish implementing logic to calculate items that need to be traded.

class Inventory:

    def __init__(self, steam_id: Union[str, int, SteamID]) -> None:
        self.steam_id = SteamID(steam_id) if not isinstance(steam_id, SteamID) else steam_id

    @cached_property
    def inventory(self) -> List[Item]:
        resp = requests.get(f"https://steamcommunity.com/inventory/{self.steam_id.as_64}/730/2?l=english&count=5000").json()
        assets: dict = resp["assets"]
        descriptions: dict = resp["descriptions"]

        items: List[Item] = []

        for item in descriptions:
            classid = item["classid"]
            asset = next((x for x in assets if x["classid"] == classid), None)
            if not asset:
                continue

            raw_exterior = next((x["value"].split("Exterior: ")[-1] for x in item["descriptions"] if x["value"].startswith("Exterior: ")), None)

            name = item["name"]
            # there may be better ways to parse this.
            exterior = Exterior(raw_exterior) if raw_exterior else None
            is_weapon = "Weapon" in (tag["category"] for tag in item["tags"])
            # right now, only csgo is supported so these are hard coded
            appid = 730
            contextid = "2"
            amount = int(asset["amount"])
            assetid = asset["assetid"]

            items.append(Item(
                name=name,
                exterior=exterior,
                is_weapon=is_weapon,
                appid=appid,
                contextid=contextid,
                amount=amount,
                assetid=assetid
            ))

        return items

    @property
    def items_to_trade(self):
        return [item for item in self.inventory if item.should_be_traded]


if __name__ == "__main__":
    print(Inventory(76561199033382814).inventory)
