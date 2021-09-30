from typing import List

from . import config
from .classes import Account, Inventory
from .types import Type


class SteamInventoryManager:

    def __init__(self):
        self.main_account: Account = config.main_account
        self.main_account.login()
        self.inventory: Inventory = Inventory(self.main_account.steam_id)
        self.alternate_accounts: List[Account] = config.alternate_accounts
        for acc in self.alternate_accounts:
            acc.login()

    def which_alternate_account(self, type: Type):
        """Finds which account the item should be traded to based on its type. Defaults to the first account in the list"""
        for acc in self.alternate_accounts:
            if acc.priority and type in acc.priority:
                return acc
        return self.alternate_accounts[0]

    def main(self):
        if not any(self.inventory.items_to_trade):
            return

        for item in self.inventory.items_to_trade:
            pass

if __name__ == "__main__":
    SteamInventoryManager().main()
