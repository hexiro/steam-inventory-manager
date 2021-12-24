import logging
from collections import defaultdict
from typing import List, Dict

from .classes import Account, Inventory
from .config import main_account, alternate_accounts
from .datatypes import ItemType, Item

logger = logging.getLogger(__name__)


class SteamInventoryManager:
    def __init__(self):
        self.main_account: Account = main_account
        logger.debug(f"{main_account=}")
        self.main_account.login()
        self.alternate_accounts: List[Account] = alternate_accounts
        for index, acc in enumerate(self.alternate_accounts, start=1):
            logger.debug(f"alternate account #{index}={acc}")
            acc.login()

        self.inventory: Inventory = Inventory(self.main_account.steam_id64)

    def which_alternate_account(self, item_type: ItemType):
        """
        Finds which account the item should be traded to based on its type.
        Defaults to the first account in the list
        """
        for acc in self.alternate_accounts:
            if acc.priorities and item_type in acc.priorities:
                return acc
        return self.alternate_accounts[0]

    def main(self):
        if not self.inventory.items_to_trade:
            logger.info("Found no items to trade.")
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
            logger.info(f"Opening trade offer with {acc.username}:")
            logger.info(f"{items=}")
            acc.accept_trade(
                partner=self.main_account,
                trade_id=trade_id,
            )
        logger.info(
            f"Successfully opened {len(trade_offers)} trade offers with {len(self.inventory.items_to_trade)} total "
            "items."
        )


if __name__ == "__main__":
    SteamInventoryManager().main()
