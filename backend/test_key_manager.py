
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(
    Path(__file__).resolve().parents[1] / ".env"
)

from encryption import generate_key
from key_manager import wrap_key, unwrap_key

dek = generate_key()

nonce, wrapped_key = wrap_key(dek)

recovered_dek = unwrap_key(nonce, wrapped_key)

assert dek == recovered_dek

print("SUCCESS: DEK protected and recovered!")