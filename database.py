import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "talentosai.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_records (
            collection TEXT NOT NULL,
            record_key TEXT NOT NULL,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (collection, record_key)
        )
    """)
    conn.commit()
    return conn


def load_collection(collection):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT record_key, payload FROM app_records WHERE collection = ?",
            (collection,),
        ).fetchall()

    result = {}
    for key, payload in rows:
        try:
            result[key] = json.loads(payload)
        except (ValueError, TypeError):
            continue
    return result


def save_collection(collection, records):
    """Replace one collection with its current records."""
    if isinstance(records, list):
        records = {
            str(item.get("Candidate_ID", item.get("Name", i))): item
            for i, item in enumerate(records)
        }

    with get_connection() as conn:
        conn.execute(
            "DELETE FROM app_records WHERE collection = ?",
            (collection,),
        )
        conn.executemany(
            """
            INSERT INTO app_records (collection, record_key, payload, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            [
                (
                    collection,
                    str(key),
                    json.dumps(value, ensure_ascii=False, default=str),
                )
                for key, value in records.items()
            ],
        )
        conn.commit()


def save_record(collection, key, value):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO app_records (collection, record_key, payload, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(collection, record_key)
            DO UPDATE SET
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                collection,
                str(key),
                json.dumps(value, ensure_ascii=False, default=str),
            ),
        )
        conn.commit()


if __name__ == "__main__":
    save_record("_test", "connection", {"status": "ok"})
    test = load_collection("_test")
    assert test["connection"]["status"] == "ok"

    with get_connection() as conn:
        conn.execute(
            "DELETE FROM app_records WHERE collection = '_test'"
        )

    print("SQLite test passed.")
    print(f"Database created at: {DB_PATH}")
