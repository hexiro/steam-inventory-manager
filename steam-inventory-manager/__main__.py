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

        self.inventory: Inventory = Inventory(self.main_account.steam_id)

    def which_alternate_account(self, type: Type):
        """Finds which account the item should be traded to based on its type. Defaults to the first account in the list"""
        for acc in self.alternate_accounts:
            if acc.priority and type in acc.priority:
                return acc
        return self.alternate_accounts[0]

    def main(self):
        if not any(self.inventory.items_to_trade):
            return

        trade_offers: Dict[Account, List[Item]] = {}

        for item in self.inventory.items_to_trade:
            acc = self.which_alternate_account(item.type)
            if acc not in trade_offers:
                trade_offers[acc] = []
            trade_offers[acc].append(item)

        trade_ids: List[str] = []

        for acc, items in trade_offers.items():
            trade_id = self.main_account.trade(
                partner=acc,
                assets=[x.trade_asset for x in items],
            )
            trade_ids.append(trade_id)
        
        pprint(trade_offers)


if __name__ == "__main__":
    SteamInventoryManager().main()
