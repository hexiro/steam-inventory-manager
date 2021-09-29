from . import config
from .classes import Account, Inventory


class SteamInventoryManager:

    def __init__(self):
        self.main_account = Account(username=config.main_account.username,
                                    password=config.main_account.password,
                                    shared_secret=config.main_account.shared_secret,
                                    identify_secret=config.main_account.identity_secret)
        self.main_account.login()
        self.inventory = Inventory(self.main_account.steam_id)

    def main(self):
        pass


if __name__ == "__main__":
    SteamInventoryManager().main()
