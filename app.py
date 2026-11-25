import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone
from io import BytesIO

from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

from backend.encryption import generate_key, encrypt_file, decrypt_file
from backend.key_manager import wrap_key, unwrap_key
from database import get_connection, initialize_database


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__, static_folder="frontend", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

initialize_database()


def current_time():
    return datetime.now(timezone.utc)


def log_event(vault_id, action):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO access_history (vault_id, action, access_time)
            VALUES (?, ?, ?)
        """, (
            vault_id,
            action,
            current_time().isoformat()
        ))


@app.route("/")
def home():
    return app.send_static_file("index.html")


# UPLOAD FILE
@app.route("/api/upload", methods=["POST"])
def upload_file():

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    original_data = file.read()

    if not original_data:
        return jsonify({"error": "File is empty"}), 400

    try:
        expiry_minutes = int(request.form.get("expiry_minutes", 60))
        max_accesses = int(request.form.get("max_accesses", 1))

        if expiry_minutes not in [5, 30, 60, 1440]:
            return jsonify({"error": "Invalid expiry time"}), 400

        if not 1 <= max_accesses <= 100:
            return jsonify({"error": "Invalid access limit"}), 400

    except ValueError:
        return jsonify({"error": "Invalid settings"}), 400

    vault_id = str(uuid.uuid4())

    dek = generate_key()

    nonce, encrypted_data = encrypt_file(original_data, dek)

    wrapped_nonce, wrapped_dek = wrap_key(dek)

    upload_time = current_time()
    expiry_time = upload_time + timedelta(minutes=expiry_minutes)

    filename = secure_filename(file.filename) or "download"

    storage_path = UPLOAD_DIR / f"{vault_id}.gk"

    try:
        storage_path.write_bytes(encrypted_data)

        with get_connection() as conn:
            conn.execute("""
                INSERT INTO vaults (
                    vault_id,
                    original_filename,
                    nonce,
                    wrapped_nonce,
                    wrapped_dek,
                    upload_time,
                    expiry_time,
                    max_accesses,
                    access_count,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'active')
            """, (
                vault_id,
                filename,
                nonce,
                wrapped_nonce,
                wrapped_dek,
                upload_time.isoformat(),
                expiry_time.isoformat(),
                max_accesses
            ))

    except Exception:
        storage_path.unlink(missing_ok=True)
        app.logger.exception("Vault creation failed")
        return jsonify({"error": "Could not create vault"}), 500

    log_event(vault_id, "UPLOAD")

    return jsonify({
        "message": "File encrypted and stored successfully",
        "file_id": vault_id,
        "vault_id": vault_id,
        "original_filename": filename,
        "expiry_time": expiry_time.isoformat(),
        "max_accesses": max_accesses,
        "encrypted": True
    }), 201


# RECOVER FILE
@app.route("/api/recover/<vault_id>", methods=["GET"])
def recover_file(vault_id):

    with get_connection() as conn:
        vault = conn.execute(
            "SELECT * FROM vaults WHERE vault_id = ?",
            (vault_id,)
        ).fetchone()

    if vault is None:
        return jsonify({"error": "Vault not found"}), 404

    if vault["status"] != "active":
        return jsonify({"error": "Vault is not active"}), 403

    if current_time() >= datetime.fromisoformat(vault["expiry_time"]):
        return jsonify({"error": "Vault has expired"}), 410

    if vault["access_count"] >= vault["max_accesses"]:
        return jsonify({"error": "Access limit reached"}), 403

    storage_path = UPLOAD_DIR / f"{vault_id}.gk"

    if not storage_path.exists():
        return jsonify({"error": "Encrypted file not found"}), 404

    try:
        encrypted_data = storage_path.read_bytes()

        dek = unwrap_key(
            vault["wrapped_nonce"],
            vault["wrapped_dek"]
        )

        original_data = decrypt_file(
            encrypted_data,
            dek,
            vault["nonce"]
        )

    except Exception:
        app.logger.exception("File recovery failed")
        return jsonify({"error": "File recovery failed"}), 500

    # Recheck access limit atomically
    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")

        updated = conn.execute("""
            UPDATE vaults
            SET access_count = access_count + 1
            WHERE vault_id = ?
              AND status = 'active'
              AND access_count < max_accesses
              AND expiry_time > ?
        """, (vault_id, current_time().isoformat()))

        if updated.rowcount != 1:
            return jsonify({
                "error": "Vault expired, revoked or access limit reached"
            }), 403

    log_event(vault_id, "RECOVER")

    return send_file(
        BytesIO(original_data),
        as_attachment=True,
        download_name=vault["original_filename"]
    )


# REVOKE ACCESS
@app.route("/api/revoke/<vault_id>", methods=["POST"])
def revoke_vault(vault_id):

    with get_connection() as conn:
        result = conn.execute("""
            UPDATE vaults
            SET status = 'revoked'
            WHERE vault_id = ? AND status = 'active'
        """, (vault_id,))

    if result.rowcount == 0:
        return jsonify({"error": "Active vault not found"}), 404

    log_event(vault_id, "REVOKE")

    return jsonify({
        "message": "Vault revoked successfully",
        "vault_id": vault_id
    }), 200


# ACCESS HISTORY
@app.route("/api/history/<vault_id>", methods=["GET"])
def get_history(vault_id):

    with get_connection() as conn:
        vault = conn.execute(
            "SELECT vault_id FROM vaults WHERE vault_id = ?",
            (vault_id,)
        ).fetchone()

        if vault is None:
            return jsonify({"error": "Vault not found"}), 404

        history = conn.execute("""
            SELECT action, access_time
            FROM access_history
            WHERE vault_id = ?
            ORDER BY access_time DESC
        """, (vault_id,)).fetchall()

    return jsonify({
        "vault_id": vault_id,
        "history": [
            {
                "action": row["action"],
                "access_time": row["access_time"]
            }
            for row in history
        ]
    }), 200


if __name__ == "__main__":
    app.run(debug=True)