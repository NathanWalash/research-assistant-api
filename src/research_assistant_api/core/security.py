import base64
import hashlib
import hmac
import os

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_KEY_LENGTH = 64
SCRYPT_SALT_LENGTH = 16


def hash_password(password: str) -> str:
    salt = os.urandom(SCRYPT_SALT_LENGTH)
    derived_key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_KEY_LENGTH,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    key_b64 = base64.b64encode(derived_key).decode("ascii")
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt_b64}${key_b64}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, n_value, r_value, p_value, salt_b64, key_b64 = password_hash.split(
            "$", maxsplit=5
        )
    except ValueError:
        return False

    if algorithm != "scrypt":
        return False

    try:
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected_key = base64.b64decode(key_b64.encode("ascii"))
        derived_key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n_value),
            r=int(r_value),
            p=int(p_value),
            dklen=len(expected_key),
        )
    except (ValueError, TypeError):
        return False

    return hmac.compare_digest(derived_key, expected_key)
