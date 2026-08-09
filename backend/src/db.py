import json
import logging
import os
import sqlite3
from datetime import datetime

logger = logging.getLogger("db")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "callers.db")


def init_db():
    """Initialize the database and create tables if they do not exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS callers (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.info("SQLite database initialized at: %s", DB_PATH)


def get_caller_by_id_or_name(user_id=None, name=None):
    """Retrieve caller details from the database by user_id or name (case-insensitive)."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    row = None

    if user_id:
        cursor.execute(
            "SELECT user_id, name, language_preference, facts, last_interaction FROM callers WHERE user_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()

    if not row and name:
        cursor.execute(
            "SELECT user_id, name, language_preference, facts, last_interaction FROM callers WHERE LOWER(name) = LOWER(?)",
            (name,),
        )
        row = cursor.fetchone()

    conn.close()

    if row:
        try:
            facts = json.loads(row[3])
        except Exception:
            facts = {}

        return {
            "user_id": row[0],
            "name": row[1],
            "language_preference": row[2],
            "facts": facts,
            "last_interaction": row[4],
        }
    return None


def upsert_caller(user_id, name, language_preference, facts):
    """Insert or update a caller's details in the database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Reuse existing user_id if the name matches to prevent duplicates
    cursor.execute("SELECT user_id FROM callers WHERE LOWER(name) = LOWER(?)", (name,))
    row = cursor.fetchone()
    if row:
        user_id = row[0]

    facts_str = json.dumps(facts)
    last_interaction = datetime.utcnow().isoformat()

    cursor.execute(
        """
        INSERT INTO callers (user_id, name, language_preference, facts, last_interaction)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name=excluded.name,
            language_preference=excluded.language_preference,
            facts=excluded.facts,
            last_interaction=excluded.last_interaction
    """,
        (user_id, name, language_preference, facts_str, last_interaction),
    )

    conn.commit()
    conn.close()
    logger.info("Caller upserted: %s (%s)", name, user_id)
