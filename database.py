import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "ghostkey.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    with get_connection() as conn:
       conn.execute("""
    CREATE TABLE IF NOT EXISTS access_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vault_id TEXT NOT NULL,
        action TEXT NOT NULL,
        access_time TEXT NOT NULL
    )
""")
       conn.execute("""
            CREATE TABLE IF NOT EXISTS vaults (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vault_id TEXT UNIQUE NOT NULL,
                original_filename TEXT NOT NULL,
                nonce BLOB NOT NULL,
                wrapped_nonce BLOB NOT NULL,
                wrapped_dek BLOB NOT NULL,
                upload_time TEXT NOT NULL,
                expiry_time TEXT NOT NULL,
                max_accesses INTEGER DEFAULT 1,
                access_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active'
            )
        """)

    conn.commit()


if __name__ == "__main__":
    initialize_database()
    print("GhostKey database initialized successfully!")