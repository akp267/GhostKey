import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path, override=False)


def get_kek():
    encoded_key = os.getenv("KEK_BASE64")

    if not encoded_key:
        raise ValueError("KEK_BASE64 is missing")

    key = base64.b64decode(encoded_key, validate=True)

    if len(key) != 32:
        raise ValueError("KEK must be exactly 32 bytes")

    return key


def wrap_key(dek):
    kek = get_kek()
    aes = AESGCM(kek)

    nonce = os.urandom(12)
    wrapped_key = aes.encrypt(nonce, dek, None)

    return nonce, wrapped_key


def unwrap_key(nonce, wrapped_key):
    kek = get_kek()
    aes = AESGCM(kek)

    return aes.decrypt(nonce, wrapped_key, None)
