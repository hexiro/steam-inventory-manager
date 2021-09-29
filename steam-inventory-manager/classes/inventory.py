from typing import Union
from functools import cached_property

import requests
from steam.steamid import SteamID

# TODO: maybe an `item` dataclass?
# TODO: finish implementing logic to calculate items that need to be traded.

class Inventory:
    PRICES = requests.get("http://csgobackpack.net/api/GetItemsList/v2/").json()["items_list"]

    def __init__(self, steam_id: Union[str, int, SteamID]) -> None:
        self.steam_id = SteamID(steam_id) if not isinstance(steam_id, SteamID) else steam_id

    @cached_property
    def inventory(self) -> list:
        resp = requests.get(f"https://steamcommunity.com/inventory/{self.steam_id.as_64}/730/2?l=english&count=5000").json()
        assets: dict = resp["assets"]
        descriptions: dict = resp["descriptions"]

        items = []

        for item in descriptions:
            classid = item["classid"]
            asset = next((x for x in assets if x["classid"] == classid), None)
            if not asset:
                continue
            item["assetid"] = asset["assetid"]
            item["instanceid"] = asset["instanceid"]

            items.append(item)

        return items