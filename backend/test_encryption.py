
from encryption import generate_key, encrypt_file, decrypt_file

original_data = b"Hello GHOSTKEY!"

key = generate_key()

nonce, encrypted_data = encrypt_file(
    original_data,
    key
)

decrypted_data = decrypt_file(
    encrypted_data,
    key,
    nonce
)

print("Original:", original_data)
print("Encrypted:", encrypted_data)
print("Decrypted:", decrypted_data)

assert original_data == decrypted_data

print("SUCCESS: Encryption and decryption working!")