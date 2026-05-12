"""Projektverwaltung — CRUD, Notizen, Next Actions."""

from datetime import datetime
from database import get_db


def list_projects(status="active"):
    """Gibt alle Projekte mit einem Status zurück."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM projects WHERE status = ? ORDER BY priority DESC", (status,)
    ).fetchall()
    conn.close()
    return rows


def get_project(name_or_id):
    """Gibt ein Projekt zurück (nach Name oder ID)."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM projects WHERE id = ? OR name LIKE ?",
        (str(name_or_id), "%" + str(name_or_id) + "%")
    ).fetchone()
    conn.close()
    return row


def create_project(name, description=None, priority=5, tags=None):
    """Erstellt ein neues Projekt."""
    conn = get_db()
    conn.execute(
        "INSERT INTO projects (name, description, priority, tags) VALUES (?, ?, ?, ?)",
        (name, description, priority, tags)
    )
    conn.commit()
    conn.close()


def update_project(project_id, **kwargs):
    """Aktualisiert Projekt-Felder (status, notes, priority, next_action, tags)."""
    allowed = {"status", "notes", "priority", "next_action", "tags", "description"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    fields["updated_at"] = datetime.now().isoformat()
    sets = ", ".join(k + " = ?" for k in fields)
    conn = get_db()
    conn.execute("UPDATE projects SET " + sets + " WHERE id = ?",
                 list(fields.values()) + [project_id])
    conn.commit()
    conn.close()


def add_project_note(project_id, note):
    """Hängt eine Notiz an ein Projekt an (mit Timestamp)."""
    conn = get_db()
    row = conn.execute("SELECT notes FROM projects WHERE id = ?", (project_id,)).fetchone()
    existing = row["notes"] or "" if row else ""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_notes = existing + "\n[" + stamp + "] " + note if existing else "[" + stamp + "] " + note
    conn.execute("UPDATE projects SET notes = ?, updated_at = ? WHERE id = ?",
                 (new_notes, datetime.now().isoformat(), project_id))
    conn.commit()
    conn.close()


def format_projects(projects):
    """Formatiert Projekte als lesbaren Text."""
    if not projects:
        return "Keine Projekte."
    lines = []
    for p in projects:
        line = "  [" + str(p["id"]) + "] " + p["name"] + " (Prio " + str(p["priority"]) + ")"
        if p["next_action"]:
            line += " → " + p["next_action"]
        lines.append(line)
    return "\n".join(lines)
