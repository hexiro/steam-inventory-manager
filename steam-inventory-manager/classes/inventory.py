from functools import cached_property
from typing import List

import requests

from ..datatypes import Exterior, Item, Type


class Inventory:
    def __init__(self, steam_id64: int) -> None:
        self.steam_id64: int = steam_id64

    @cached_property
    def items(self) -> List[Item]:
        resp = requests.get(f"https://steamcommunity.com/inventory/{self.steam_id64}/730/2?l=english&count=5000").json()
        assets: dict = resp["assets"]
        descriptions: dict = resp["descriptions"]

        items: List[Item] = []

        for asset in assets:
            # ex. {'appid': 730, 'contextid': '2', 'assetid': '23603986921', 'classid': '4593998508', 'instanceid':
            # '519977179', 'amount': '1'}
            classid = asset["classid"]
            description = next((x for x in descriptions if x["classid"] == classid), None)
            # this means that the item isn't currently tradable.
            # sometimes the item will never be tradable and other times it will be tradable after 7 days.
            if description["tradable"] == 0:
                continue

            type_values = [x.value for x in Type]
            # there may be better ways to parse this.
            exterior_value: List[str] = [
                x["value"] for x in description["descriptions"] if x["value"].startswith("Exterior: ")
            ]
            type_value: List[str] = [x["localized_tag_name"] for x in description["tags"] if x["category"] == "Type"]

            raw_exterior: str = exterior_value[0].split("Exterior: ")[-1] if exterior_value else None
            raw_type: str = type_value[0] if type_value and type_value[0] in type_values else None

            name = description["name"]
            # right now, only csgo is supported so these are hard coded
            appid = 730
            contextid = "2"
            amount = int(asset["amount"])
            assetid = asset["assetid"]
            # optionals
            exterior = Exterior(raw_exterior) if raw_exterior else None
            type = Type(raw_type) if raw_type else None

            items.append(
                Item(
                    name=name,
                    appid=appid,
                    contextid=contextid,
                    amount=amount,
                    assetid=assetid,
                    exterior=exterior,
                    type=type,
                )
            )

        return items

    @cached_property
    def items_to_trade(self):
        return [item for item in self.items if item.should_be_traded]
