import requests


class SteamInventoryManagerError(Exception):
    """ Base Exception class for this project. """


class TradeError(SteamInventoryManagerError):
    """ Raises When a trade fails to be sent """


class RequestError(requests.RequestException):
    """ Raises when a web request fails to complete. """


class ConfigurationError(SteamInventoryManagerError):
    """ Raises when the config.yaml file has issues which cannot be ignored. """


class LoginError(SteamInventoryManagerError):
    """ Raises when the client fails to login to steam. """


class IncorrectPassword(LoginError):
    """ Raises when the client's specified password is incorrect """


class TwoFactorCodeInvalid(LoginError):
    """ Raises when the generate 2fa code doesn't work. (each code can only be used once; new code every 30 seconds) """


class CaptchaRequired(LoginError):
    """ Raises when steam is asking the client for a captcha to be able to log in. """


class EmailCodeRequired(LoginError):
    """ Raises when an account has email verification enabled instead of mobile verification. """
