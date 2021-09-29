import pathlib

import yaml


config_file = pathlib.Path(__file__).parents[2] / "config.yaml"
config = yaml.safe_load(config_file.read_text(encoding="utf-8"))

managed_account = config["managed-account"]
secondary_accounts = config["secondary-accounts"]
options = config["options"]