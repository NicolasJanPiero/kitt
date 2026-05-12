"""Langzeitgedächtnis — Speichern, Suchen, Konversationshistorie."""

from database import get_db


def save_memory(type, content, source="user", tags=None, entity=None,
                importance=5, session_id=None):
    """Speichert einen Memory-Eintrag."""
    conn = get_db()
    conn.execute(
        "INSERT INTO memory (type, content, source, tags, entity_name, importance, session_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (type, content, source, tags, entity, importance, session_id)
    )
    conn.commit()
    conn.close()


def search_memory(query, type=None, limit=10):
    """Sucht in Memories (LIKE auf content und tags)."""
    conn = get_db()
    sql = "SELECT * FROM memory WHERE (content LIKE ? OR tags LIKE ?)"
    params = ["%" + query + "%", "%" + query + "%"]
    if type:
        sql += " AND type = ?"
        params.append(type)
    sql += " ORDER BY importance DESC, created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def get_recent_memories(type=None, limit=20):
    """Gibt die neuesten Memories zurück."""
    conn = get_db()
    if type:
        rows = conn.execute(
            "SELECT * FROM memory WHERE type = ? ORDER BY created_at DESC LIMIT ?",
            (type, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM memory ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return rows


def get_conversation_history(session_id, limit=20):
    """Gibt die Konversationshistorie einer Session zurück."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM memory WHERE type='conversation' AND session_id = ? "
        "ORDER BY created_at ASC LIMIT ?",
        (session_id, limit)
    ).fetchall()
    conn.close()
    return rows


def get_context_for_prompt(limit_facts=5, limit_prefs=3, limit_projects=5):
    """Lädt relevanten Kontext für den System-Prompt."""
    conn = get_db()
    facts = conn.execute(
        "SELECT content FROM memory WHERE type='fact' ORDER BY importance DESC, created_at DESC LIMIT ?",
        (limit_facts,)
    ).fetchall()
    prefs = conn.execute(
        "SELECT content FROM memory WHERE type='preference' ORDER BY created_at DESC LIMIT ?",
        (limit_prefs,)
    ).fetchall()
    projects = conn.execute(
        "SELECT name, status, next_action FROM projects WHERE status='active' ORDER BY priority DESC LIMIT ?",
        (limit_projects,)
    ).fetchall()
    conn.close()

    lines = []
    if facts:
        lines.append("Fakten: " + " | ".join(r["content"] for r in facts))
    if prefs:
        lines.append("Vorlieben: " + " | ".join(r["content"] for r in prefs))
    if projects:
        lines.append("Projekte: " + " | ".join(
            r["name"] + " (" + (r["next_action"] or "kein nächster Schritt") + ")"
            for r in projects
        ))
    return "\n".join(lines)


def cleanup_expired():
    """Löscht abgelaufene Memories."""
    conn = get_db()
    conn.execute("DELETE FROM memory WHERE expires_at IS NOT NULL AND expires_at < datetime('now')")
    conn.commit()
    conn.close()
