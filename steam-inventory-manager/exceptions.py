import requests


class SteamInventoryManagerException(Exception):
    """ Base Exception class for this project. """


class RequestException(requests.RequestException):
    """ Raises when a web request fails to complete. """


class ConfigurationError(SteamInventoryManagerException):
    """ Raises when the config.yaml file has issues which cannot be ignored. """


class LoginError(SteamInventoryManagerException):
    """ Raises when the client fails to login to steam. """


class IncorrectPassword(LoginError):
    """ Raises when the client's specified password is incorrect """


class TwoFactorCodeInvalid(LoginError):
    """ Raises when the generate 2fa code doesn't work. (each code can only be used once; new code every 30 seconds) """


class CaptchaRequired(LoginError):
    """ Raises when steam is asking the client for a captcha to be able to log in. """
