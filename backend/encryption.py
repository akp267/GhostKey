import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_key():
    return AESGCM.generate_key(bit_length=256)


def encrypt_file(file_data, key):
    aes = AESGCM(key)
    nonce = os.urandom(12)

    encrypted_data = aes.encrypt(
        nonce,
        file_data,
        None
    )

    return nonce, encrypted_data


def decrypt_file(encrypted_data, key, nonce):
    aes = AESGCM(key)

    decrypted_data = aes.decrypt(
        nonce,
        encrypted_data,
        None
    )

    return decrypted_data