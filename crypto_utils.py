import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_key():
    """Generate a secure 256-bit encryption key."""
    return AESGCM.generate_key(bit_length=256)


def encrypt_data(data, key):
    """Encrypt file data using AES-256-GCM."""

    aes = AESGCM(key)

    # Generate a unique 12-byte nonce
    nonce = os.urandom(12)

    # Encrypt the data
    encrypted_data = aes.encrypt(nonce, data, None)

    return nonce, encrypted_data


def decrypt_data(nonce, encrypted_data, key):
    """Decrypt data using AES-256-GCM."""

    aes = AESGCM(key)

    return aes.decrypt(nonce, encrypted_data, None)