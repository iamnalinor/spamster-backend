import base64
import secrets

import scrypt


def rand_string() -> str:
    return secrets.token_urlsafe(32)


def hash_password(password: str, salt: str) -> str:
    data = scrypt.hash(password, salt, N=1 << 14, r=8, p=1, buflen=64)
    return base64.b64encode(data).decode()
