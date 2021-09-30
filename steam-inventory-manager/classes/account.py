import base64
import datetime
import json
from typing import Optional, Tuple, List, Type

import requests
import rsa
from steam.steamid import SteamID

from ..exceptions import RequestError, IncorrectPassword, LoginError, CaptchaRequired, EmailCodeRequired, TwoFactorCodeInvalid
from ..utils import generate_session_id, do_no_cache, generate_one_time_code


class Account:

    def __init__(self, username: str, password: str, *, shared_secret: str, identity_secret: str, priority: List[Type] = None):
        self._username: str = username
        self._password: str = password
        self._shared_secret: str = shared_secret
        self._identity_secret: str = identity_secret
        self._logged_in: bool = False
        self._steam_id: Optional[SteamID] = None
        self._session = requests.Session()
        self._session.headers["User-Agent"] = "python steam-inventory-manager/v1.0.0"
        self._session_id = None
        self._public_key, self._timestamp = self._rsa_key()
        self.priority = priority

    def __repr__(self):
        return (f"<{self.__class__.__name__} "
                f"username={self.username!r} "
                f"password={self.password!r} "
                f"shared_secret={self.shared_secret!r} "
                f"identify_secret={self.identity_secret!r}"
                f">")

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
    def steam_id(self) -> SteamID:
        return self._steam_id

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

    def transfer_cookie(self, name: str, value: str):
        """ sets a cookie for the three main steam domains """
        for domain in ["store.steampowered.com", "help.steampowered.com", "steamcommunity.com"]:
            self.session.cookies.set(name, value, domain=domain, secure=True)

    @property
    def encrypted_password(self):
        return base64.b64encode(rsa.encrypt(self.password.encode("utf8"), self.public_key)).decode("utf8")

    def login(self):
        if self.logged_in:
            return self.session

        if not self.password:
            raise IncorrectPassword("password not specified")

        attempt = self._attempt_login()

        if attempt.get("success", False) and attempt.get("login_complete"):
            # successfully logged in
            self._logged_in = True

            for cookie in list(self.session.cookies):
                self.transfer_cookie(cookie.name, cookie.value)

            self._session_id = generate_session_id()
            self.transfer_cookie("sessionid", self.session_id)

            transfer_parameters = attempt["transfer_parameters"]
            self._steam_id = SteamID(transfer_parameters["steamid"])
            return

        email_required = attempt.get("emailauth_needed", False)
        captcha_required = attempt.get("captcha_needed", False)
        two_factor_required = attempt.get("requires_twofactor", False)
        password_incorrect = attempt.get('clear_password_field', False)
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
            'username': self.username,
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
            resp = self.session.post("https://steamcommunity.com/login/getrsakey/", timeout=15, data={
                "username": self.username,
                "donotcache": do_no_cache()
            }).json()
            mod = int(resp["publickey_mod"], 16)
            exp = int(resp["publickey_exp"], 16)
            timestamp = resp["timestamp"]
            return rsa.PublicKey(mod, exp), timestamp
        except requests.exceptions.RequestException as e:
            raise RequestError(str(e))
        except KeyError:
            raise LoginError("Unable to retrieve RSA keys from steam.")
