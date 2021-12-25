from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING

from .classes import Account, Inventory
from .config import main_account, alternate_accounts
from .utils import parse_priorities

if TYPE_CHECKING:
    from .datatypes import ItemType, Item

logger = logging.getLogger(__name__)


class SteamInventoryManager:
    def __init__(self):
        self.main_account: Account = Account(
            username=main_account["username"],
            password=main_account["password"],
            shared_secret=main_account["shared-secret"],
            identity_secret=main_account["identity-secret"],
        )
        logger.debug(f"{main_account=}")
        self.main_account.login()

        self.alternate_accounts: list[Account] = []
        for config_acc in alternate_accounts:
            self.alternate_accounts.append(
                Account(
                    username=config_acc["username"],
                    password=config_acc["password"],
                    shared_secret=config_acc["shared-secret"],
                    priorities=parse_priorities(config_acc.get("priorities")),
                )
            )

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

        logger.debug(f"items_to_trade={self.inventory.items_to_trade}")

        trade_offers: dict[Account, list[Item]] = defaultdict(list)

        for item in self.inventory.items_to_trade:
            acc = self.which_alternate_account(item.type)
            trade_offers[acc].append(item)

        for acc, items in trade_offers.items():
            trade_id = self.main_account.trade(
                partner=acc,
                me=[item.trade_asset for item in items],
            )
            logger.info(f"Opening trade offer with {acc.username}:")
            logger.info(f"items={[item.name for item in items]}")
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
