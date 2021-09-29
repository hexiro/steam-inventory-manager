import base64
import hmac
import secrets
import struct
import time
from hashlib import sha1
from time import time

import requests

PRICES = requests.get("https://csgobackpack.net/api/GetItemsList/v2/").json()["items_list"]


# contains snippets from
# https://github.com/Gobot1234/steam.py/blob/4af51e42c5357c90bfc476a098b900541ded1a3c/steam/guard.py


def generate_session_id() -> str:
    """Generates a Steam session id."""
    return secrets.token_hex(16)


def do_no_cache():
    """Generates a "donotcache" value to be used on steam. Not really sure if this proper."""
    return int(time() * 1000) - (18 * 60 * 60)


def generate_one_time_code(shared_secret: str) -> str:
    """Generate a Steam Guard code for signing in."""
    timestamp = int(time())
    time_buffer = struct.pack(">Q", timestamp // 30)  # pack as Big endian, uint64
    time_hmac = hmac.new(base64.b64decode(shared_secret), time_buffer, digestmod=sha1).digest()
    begin = ord(time_hmac[19:20]) & 0xF
    full_code = struct.unpack(">I", time_hmac[begin: begin + 4])[0] & 0x7FFFFFFF  # unpack as Big endian uint32
    chars = "23456789BCDFGHJKMNPQRTVWXY"
    code = []
    for _ in range(5):
        full_code, i = divmod(full_code, len(chars))
        code.append(chars[i])
    return "".join(code)


def generate_device_id(user_id64: int) -> str:
    """
    Generate the device id for a user's 64 bit ID.
    (it works, however it's different that one generated from mobile app)
    """
    hexed_steam_id = sha1(str(int(user_id64)).encode("ascii")).hexdigest()
    print(hexed_steam_id)
    partial_id = (
        hexed_steam_id[:8],
        hexed_steam_id[8:12],
        hexed_steam_id[12:16],
        hexed_steam_id[16:20],
        hexed_steam_id[20:32],
    )
    return f'android:{"-".join(partial_id)}'


# print(generate_device_id(76561199033382814))


def generate_confirmation_code(identity_secret: str, tag: str) -> str:
    """Generate a trade confirmation code.
    """
    timestamp = int(time())
    buffer = struct.pack(">Q", timestamp) + tag.encode("ascii")
    return base64.b64encode(hmac.new(base64.b64decode(identity_secret), buffer, digestmod=sha1).digest()).decode()
