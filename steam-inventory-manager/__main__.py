from collections import defaultdict
from typing import List, Dict

from . import config
from .classes import Account, Inventory
from .types import Type, Item


class SteamInventoryManager:

    def __init__(self):
        self.main_account: Account = config.main_account
        self.main_account.login()
        self.alternate_accounts: List[Account] = config.alternate_accounts
        for acc in self.alternate_accounts:
            acc.login()

        self.inventory: Inventory = Inventory(self.main_account.steam_id64)

    def which_alternate_account(self, type: Type):
        """
        Finds which account the item should be traded to based on its type.
        Defaults to the first account in the list
        """
        for acc in self.alternate_accounts:
            if acc.priority and type in acc.priority:
                return acc
        return self.alternate_accounts[0]

    def main(self):
        if not self.inventory.items_to_trade:
            print("Found no items to trade.")
            return

        trade_offers: Dict[Account, List[Item]] = defaultdict(list)

        for item in self.inventory.items_to_trade:
            acc = self.which_alternate_account(item.type)
            trade_offers[acc].append(item.trade_asset)

        for acc, items in trade_offers.items():
            trade_id = self.main_account.trade(
                partner=acc,
                me=items,
            )
            acc.accept_trade(
                partner=self.main_account,
                trade_id=trade_id,
            )
        print(f"Successfully opened {len(trade_offers)} trade offers with {len(self.inventory.items_to_trade)} total "
              "items.")


if __name__ == "__main__":
    SteamInventoryManager().main()
