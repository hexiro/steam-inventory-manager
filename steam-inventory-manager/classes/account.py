import base64
import datetime
import json
from functools import cached_property
from time import time
from typing import Optional, Tuple, List, Any, Dict

import requests
import rsa
from bs4 import BeautifulSoup

from .. import cache
from ..datatypes import TradeConfirmation, ItemType
from ..exceptions import (
    RequestError,
    IncorrectPassword,
    LoginError,
    CaptchaRequired,
    EmailCodeRequired,
    TwoFactorCodeInvalid,
    TradeError,
    CredentialsError,
)
from ..utils import (
    generate_session_id,
    do_no_cache,
    generate_one_time_code,
    generate_device_id,
    generate_confirmation_code,
)


class Account:
    def __init__(
        self,
        username: str,
        password: str,
        *,
        shared_secret: str,
        identity_secret: Optional[str] = None,
        priorities: Optional[List[ItemType]] = None,
    ):
        self._username: str = username
        self._password: str = password
        self._shared_secret: str = shared_secret
        self._identity_secret: Optional[str] = identity_secret
        self._logged_in: bool = False
        self._steam_id64: Optional[int] = None
        self._session = requests.Session()
        self._session.headers["User-Agent"] = "python steam-inventory-manager/v1.0.0"
        self._session_id: Optional[str] = None
        self._public_key, self._timestamp = self._rsa_key()
        self._priorities: List[ItemType] = priorities or []
        self._confirmations: Dict[int, TradeConfirmation] = {}

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} "
            f"username={self.username!r} "
            f"password={self.password!r} "
            f"shared_secret={self.shared_secret!r} "
            f"identify_secret={self.identity_secret!r}"
            f">"
        )

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, new_password: str):
        if not self.logged_in:
            self._password = new_password

    @property
    def shared_secret(self) -> str:
        return self._shared_secret

    @property
    def identity_secret(self) -> str:
        return self._identity_secret

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    @property
    def steam_id64(self) -> int:
        return self._steam_id64

    @property
    def session(self):
        return self._session

    @property
    def session_id(self) -> str:
        return self._shared_secret

    @property
    def public_key(self) -> rsa.PublicKey:
        return self._public_key

    @property
    def timestamp(self) -> datetime.datetime:
        return self._timestamp

    @property
    def priorities(self) -> List[ItemType]:
        return self._priorities

    @property
    def encrypted_password(self):
        return base64.b64encode(rsa.encrypt(self.password.encode("utf8"), self.public_key)).decode("utf8")

    @cached_property
    def trade_token(self):
        privacy_page = self.session.get(f"https://steamcommunity.com/profiles/{self.steam_id64}/tradeoffers/privacy")
        soup = BeautifulSoup(privacy_page.text, "html.parser")
        trade_link = soup.find("input", {"id": "trade_offer_access_url"}).attrs["value"]
        return trade_link.split("&token=")[-1]

    def trade(self, partner: "Account", me: list = None, them: list = None) -> int:
        """Sends a trade an returns the trade id"""
        payload = {
            "sessionid": self.session_id,
            "serverid": 1,
            "partner": partner.steam_id64,
            "tradeoffermessage": f"Trade created by steam-inventory-manager on {datetime.datetime.now():%x at %X}",
            "json_tradeoffer": json.dumps(
                {
                    "newversion": "true",
                    "version": 2,
                    "me": {"assets": me or [], "currency": [], "ready": "false"},
                    "them": {"assets": them or [], "currency": [], "ready": "false"},
                }
            ),
            "captcha": "",
            "trade_offer_create_params": json.dumps({"trade_offer_access_token": partner.trade_token}),
        }
        headers = {"Referer": "https://steamcommunity.com/tradeoffer/new/"}
        tradeoffer = self.session.post(
            "https://steamcommunity.com/tradeoffer/new/send", data=payload, headers=headers
        ).json()

        if tradeoffer.get("strError"):
            raise TradeError(tradeoffer["strError"])

        trade_id = int(tradeoffer["tradeofferid"])
        self._confirm_trade(trade_id, tradeoffer)
        return trade_id

    def accept_trade(self, partner: "Account", trade_id: int):
        payload = {
            "sessionid": self.session_id,
            "tradeofferid": trade_id,
            "serverid": 1,
            "partner": partner.steam_id64,
            "captcha": "",
        }
        headers = {"Referer": f"https://steamcommunity.com/tradeoffer/{trade_id}"}
        resp = self.session.post(
            f"https://steamcommunity.com/tradeoffer/{trade_id}/accept", data=payload, headers=headers
        ).json()
        # confirmation shouldn't be needed as `needs_mobile_confirmation` will be False
        # if no items are present of this account's side
        self._confirm_trade(trade_id, resp)

    def _confirm_trade(self, trade_id: int, tradeoffer_resp: dict):
        if tradeoffer_resp.get("needs_mobile_confirmation", False):
            self._fetch_confirmations()
            confirmation = self._confirmations.get(trade_id)
            timestamp = int(time())
            device_id = generate_device_id(self.steam_id64)
            params = {
                "p": device_id,
                "a": self.steam_id64,
                "k": generate_confirmation_code(self.identity_secret, "allow", timestamp),
                "t": timestamp,
                "m": "android",
                "tag": "allow",
                "op": "allow",
                "cid": confirmation.data_conf_id,
                "ck": confirmation.data_key,
            }
            resp = self.session.get("https://steamcommunity.com/mobileconf/ajaxop", params=params).json()

            if not resp.get("success", False):
                raise TradeError("Failed to accept trade.")

    def login(self):
        if self.logged_in:
            return self.session

        self._restore_session()
        if self.logged_in:
            return self.session

        if not self.password:
            raise IncorrectPassword("password not specified")

        attempt = self._attempt_login()

        if attempt.get("success", False) and attempt.get("login_complete"):
            # successfully logged in
            self._logged_in = True

            for cookie in list(self.session.cookies):
                self._transfer_cookie(cookie.name, cookie.value)

            self._session_id = generate_session_id()
            self._transfer_cookie("sessionid", self.session_id)

            transfer_parameters = attempt["transfer_parameters"]
            self._steam_id64 = transfer_parameters["steamid"]
            self._log_session()
            return

        email_required = attempt.get("emailauth_needed", False)
        captcha_required = attempt.get("captcha_needed", False)
        two_factor_required = attempt.get("requires_twofactor", False)
        password_incorrect = attempt.get("clear_password_field", False)
        message = attempt["message"]

        if captcha_required:
            raise CaptchaRequired(message)
        elif password_incorrect:
            raise IncorrectPassword(message)
        elif two_factor_required:
            raise TwoFactorCodeInvalid(message)
        elif email_required:
            raise EmailCodeRequired("Email Authentication not supported.")
        # sometimes the error message will match
        # 'There have been too many login failures from your network in a short time period.'
        # 'Please wait and try again later.'
        raise LoginError(message)

    def _attempt_login(self):
        data = {
            "username": self.username,
            "password": self.encrypted_password,
            "emailauth": "",
            "emailsteamid": "",
            "twofactorcode": generate_one_time_code(self.shared_secret),
            "captchagid": -1,
            "captcha_text": "",
            "loginfriendlyname": self.session.headers["User-Agent"],
            "rsatimestamp": self.timestamp,
            "remember_login": "true",
            "donotcache": do_no_cache(),
        }
        try:
            return self.session.post("https://steamcommunity.com/login/dologin/", data=data, timeout=15).json()
        except requests.exceptions.RequestException as e:
            raise RequestError(str(e))
        except json.JSONDecodeError as e:
            raise LoginError(str(e))

    def _rsa_key(self) -> Tuple[rsa.PublicKey, datetime.datetime]:
        try:
            resp = self.session.post(
                "https://steamcommunity.com/login/getrsakey/",
                timeout=15,
                data={"username": self.username, "donotcache": do_no_cache()},
            ).json()
            mod = int(resp["publickey_mod"], 16)
            exp = int(resp["publickey_exp"], 16)
            timestamp = resp["timestamp"]
            return rsa.PublicKey(mod, exp), timestamp
        except requests.exceptions.RequestException as e:
            raise RequestError(str(e))
        except KeyError:
            raise LoginError("Unable to retrieve RSA keys from steam.")

    def _transfer_cookie(self, name: str, value: str):
        """sets a cookie for the three main steam domains"""
        for domain in ["store.steampowered.com", "help.steampowered.com", "steamcommunity.com"]:
            self.session.cookies.set(name, value, domain=domain, secure=True)

    def _create_confirmation_params(self, tag: str) -> Dict[str, Any]:
        timestamp = int(time())
        return {
            "p": generate_device_id(self.steam_id64),
            "a": self.steam_id64,
            "k": generate_confirmation_code(self.identity_secret, tag, timestamp),
            "t": timestamp,
            "m": "android",
            "tag": tag,
        }

    def _fetch_confirmations(self):
        params = self._create_confirmation_params("conf")
        headers = {"X-Requested-With": "com.valvesoftware.android.steam.community"}
        resp = self.session.get("https://steamcommunity.com/mobileconf/conf", params=params, headers=headers).text

        if "incorrect Steam Guard codes." in resp:
            raise CredentialsError("identity_secret is incorrect")
        if "Oh nooooooes!" in resp:
            raise TradeError("Failed to accept trade.")

        soup = BeautifulSoup(resp, "html.parser")
        if soup.select("#mobileconf_empty"):
            return self._confirmations
        for confirmation in soup.select("#mobileconf_list .mobileconf_list_entry"):
            data_conf_id = confirmation["data-confid"]
            key = confirmation["data-key"]
            trade_id = int(confirmation.get("data-creator", 0))
            confirmation_id = confirmation["id"].split("conf")[1]
            self._confirmations[trade_id] = TradeConfirmation(confirmation_id, data_conf_id, key, trade_id)
        return self._confirmations

    def _is_logged_in(self) -> bool:
        resp = self.session.get("https://steamcommunity.com/my/profile")
        # redirects to profile if logged in else brings you to login page
        return "login/home" not in resp.url

    def _restore_session(self):
        account_data = cache.session_data(self.username)
        if not account_data:
            return
        session_id = account_data.get("session_id")
        steam_id64 = account_data.get("steam_id64")
        steam_login_secure = account_data.get("steam_login_secure")
        if session_id:
            self._session_id = session_id
            self._transfer_cookie("sessionid", self.session_id)
        if steam_id64:
            self._steam_id64 = steam_id64
        if steam_login_secure:
            self._transfer_cookie(name="steamLoginSecure", value=steam_login_secure)
        if self._is_logged_in():
            self._logged_in = True

    def _log_session(self):
        steam_login_secure = self.session.cookies.get(name="steamLoginSecure", domain="steamcommunity.com")
        # this should always be set, but just in case, we don't want to set bad data in the json file.
        if steam_login_secure and self.session_id and self.steam_id64:
            cache.store_session_data(
                self.username,
                session_id=self.session_id,
                steam_id64=self.steam_id64,
                steam_login_secure=steam_login_secure,
            )
