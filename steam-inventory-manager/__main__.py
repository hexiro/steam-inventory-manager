from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING

from .account import Account
from .config import main_account, alternate_accounts
from .inventory import Inventory
from .logger import setup
from .utils import parse_priorities

if TYPE_CHECKING:
    from .datatypes import ItemType, Item

setup()
logger = logging.getLogger(__name__)


class SteamInventoryManager:
    def __init__(self):
        self.main_account: Account = Account(
            username=main_account["username"],
            password=main_account["password"],
            shared_secret=main_account["shared-secret"],
            identity_secret=main_account["identity-secret"],
        )
        self.main_account.login()

        self.alternate_accounts: list[Account] = []
        for config_acc in alternate_accounts:
            acc = Account(
                username=config_acc["username"],
                password=config_acc["password"],
                shared_secret=config_acc["shared-secret"],
                priorities=parse_priorities(config_acc.get("priorities")),
            )
            acc.login()
            self.alternate_accounts.append(acc)

        self.inventory = Inventory(self.main_account.steam_id64)

    def which_alternate_account(self, item_type: ItemType):
        """
        Finds which account the item should be traded to based on its type.
        Defaults to the first account in the list
        """
        for acc in self.alternate_accounts:
            if acc.priorities and item_type in acc.priorities:
                return acc
        return self.alternate_accounts[0]

    def main(self) -> None:
        logger.info(f"Main account: {self.main_account.username}")

        for index, acc in enumerate(self.alternate_accounts, start=1):
            logger.info(f"Alternate account #{index}: {acc.username}")

        logger.info("All accounts logged in!")

        if not self.inventory.items_to_trade:
            logger.critical("Found no items to trade.")
            return

        trade_offers: dict[Account, list[Item]] = defaultdict(list)

        for item in self.inventory.items_to_trade:
            acc = self.which_alternate_account(item.type)
            trade_offers[acc].append(item)

        for acc, items in trade_offers.items():
            trade_id = self.main_account.trade(
                partner=acc,
                me=[item.trade_asset for item in items],
            )
            logger.info(f"Opening trade offer with: {acc.username}")
            logger.info(f"Items being traded: {', '.join(i.market_name for i in self.inventory.items_to_trade)}")
            acc.accept_trade(
                partner=self.main_account,
                trade_id=trade_id,
            )
        len_offers = len(trade_offers)
        len_items = len(self.inventory.items_to_trade)
        offers_noun = "offers" if len_offers > 1 else "offer"
        items_noun = "items" if len_items > 1 else "item"

        logger.info(f"Successfully opened {len_offers} trade {offers_noun} with {len_offers} total {items_noun}.")


if __name__ == "__main__":
    SteamInventoryManager().main()
