from collections import defaultdict
from pprint import pprint
from typing import List, Dict

from . import config
from .classes import Account, Inventory
from .types import Type, Item


class SteamInventoryManager:

    def __init__(self):
        self.main_account: Account = config.main_account
        self.main_account.login()
        print(self.main_account.trade_token)
        self.alternate_accounts: List[Account] = config.alternate_accounts
        for acc in self.alternate_accounts:
            acc.login()
            print(acc.trade_token)

        self.inventory: Inventory = Inventory(self.main_account.steam_id64)

    def which_alternate_account(self, type: Type):
        """Finds which account the item should be traded to based on its type. Defaults to the first account in the list"""
        for acc in self.alternate_accounts:
            if acc.priority and type in acc.priority:
                return acc
        return self.alternate_accounts[0]

    def main(self):
        if not any(self.inventory.items_to_trade):
            return

        trade_offers: Dict[Account, List[Item]] = defaultdict(list)

        for item in self.inventory.items_to_trade:
            acc = self.which_alternate_account(item.type)
            trade_offers[acc].append(item.trade_asset)

        trade_offers = dict(trade_offers)
        pprint(trade_offers)

        for acc, items in trade_offers.items():

            # TODO: add THEM / ME fields to make it so main account can send trades
            # so 2nd account doesn't need an identity secret.

            trade_id = acc.trade(
                partner=self.main_account,
                assets=items,
            )
            # acc.accept_trade(
            #     partner=self.main_account,
            #     trade_id=trade_id,
            # )


if __name__ == "__main__":
    SteamInventoryManager().main()
    # inv = Inventory(SteamID(76561199033382814))
    #
    # for item in inv.items:
    #     print(item.should_be_traded, repr(item))

    # total_items = len(inv.items)
    # should_be_traded = len([i for i in inv.items if i.should_be_traded])
    # print(f"{should_be_traded}/{total_items}")