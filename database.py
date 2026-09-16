"""
Tiny SQLite persistence layer — no ORM, just sqlite3, so it's easy to read,
debug, and inspect directly with `sqlite3 chipin.db` if something looks off.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "chipin.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    pool_name TEXT NOT NULL DEFAULT '',
    target REAL NOT NULL DEFAULT 6000,
    organiser TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    amount REAL NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.execute(
            "INSERT OR IGNORE INTO settings (id, pool_name, target, organiser) VALUES (1, '', 6000, '')"
        )
        conn.commit()
    finally:
        conn.close()


def update_member_name(member_id: int, name: str) -> None:
    conn = get_connection()
    try:
        conn.execute("UPDATE members SET name = ? WHERE id = ?", (name, member_id))
        conn.commit()
    finally:
        conn.close()


def update_payment(payment_id: int, amount: float, note: str) -> None:
    conn = get_connection()
    try:
        conn.execute("UPDATE payments SET amount = ?, note = ? WHERE id = ?", (amount, note, payment_id))
        conn.commit()
    finally:
        conn.close()


def reset_db() -> None:
    """Wipe every table but keep the schema — used by the /api/reset endpoint."""
    conn = get_connection()
    try:
        conn.executescript(
            "DELETE FROM payments; DELETE FROM members; "
            "UPDATE settings SET pool_name='', target=6000, organiser='' WHERE id=1;"
        )
        conn.commit()
    finally:
        conn.close()
