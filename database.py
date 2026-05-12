"""Datenbank-Modul — SQLite Connection, Schema-Init, Migration."""

import os
import shutil
import sqlite3
from config import DB_PATH

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")
SEED_PATH = os.path.join(os.path.dirname(__file__), "seed.sql")
SCHEMA_VERSION = "1"


def get_db():
    """Gibt eine DB-Connection zurück (mit Row-Factory)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Erstellt Schema und Seed-Daten wenn DB neu ist."""
    is_new = not os.path.exists(DB_PATH)
    conn = get_db()

    if is_new:
        # Schema laden
        with open(SCHEMA_PATH) as f:
            conn.executescript(f.read())
        # Seed-Daten laden
        if os.path.exists(SEED_PATH):
            with open(SEED_PATH) as f:
                conn.executescript(f.read())
        conn.close()
        return True

    # Bestehende DB: Schema-Version prüfen
    try:
        row = conn.execute("SELECT value FROM soul WHERE key='schema_version'").fetchone()
        if row and row["value"] != SCHEMA_VERSION:
            backup_db()
            print("WARNUNG: Schema-Version " + row["value"] + " != " + SCHEMA_VERSION)
    except sqlite3.OperationalError:
        # soul-Tabelle existiert nicht — frische DB, Schema laden
        with open(SCHEMA_PATH) as f:
            conn.executescript(f.read())
        if os.path.exists(SEED_PATH):
            with open(SEED_PATH) as f:
                conn.executescript(f.read())

    conn.close()
    return False


def backup_db():
    """Erstellt ein Backup der Datenbank."""
    if os.path.exists(DB_PATH):
        backup = DB_PATH + ".backup"
        shutil.copy2(DB_PATH, backup)
        return backup
    return None


def log_to_db(action, input_text=None, output_text=None, confirmed=None,
              channel="terminal", module=None, data_class=None, duration_ms=None):
    """Schreibt einen Log-Eintrag in die logs-Tabelle."""
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO logs (action, input, output, confirmed, channel, module, data_class, duration_ms) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (action, input_text, output_text, confirmed, channel, module, data_class, duration_ms)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error:
        pass  # Logging darf nie den Agent crashen
