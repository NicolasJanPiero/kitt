"""Task-Management — CRUD, Prioritäten, Recurring."""

from datetime import datetime
from database import get_db

PRIORITY_ORDER = {"urgent": 0, "high": 1, "medium": 2, "low": 3}


def list_tasks(status="open", project_id=None, category=None, limit=20):
    """Gibt Tasks zurück, sortiert nach Priorität dann Fälligkeit."""
    conn = get_db()
    sql = "SELECT t.*, p.name as project_name FROM tasks t LEFT JOIN projects p ON t.project_id = p.id WHERE t.status = ?"
    params = [status]
    if project_id:
        sql += " AND t.project_id = ?"
        params.append(project_id)
    if category:
        sql += " AND t.category = ?"
        params.append(category)
    sql += " ORDER BY CASE t.priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, t.due_date ASC NULLS LAST LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def create_task(title, project_id=None, priority="medium", category="arbeit",
                due_date=None, energy_level=None, description=None):
    """Erstellt einen neuen Task."""
    conn = get_db()
    conn.execute(
        "INSERT INTO tasks (title, project_id, priority, category, due_date, energy_level, description) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title, project_id, priority, category, due_date, energy_level, description)
    )
    conn.commit()
    conn.close()


def complete_task(task_id):
    """Markiert einen Task als erledigt."""
    conn = get_db()
    conn.execute("UPDATE tasks SET status = 'done', completed_at = ? WHERE id = ?",
                 (datetime.now().isoformat(), task_id))
    conn.commit()
    conn.close()


def defer_task(task_id, new_due_date=None):
    """Verschiebt einen Task."""
    conn = get_db()
    conn.execute("UPDATE tasks SET status = 'deferred' WHERE id = ?", (task_id,))
    if new_due_date:
        conn.execute("UPDATE tasks SET due_date = ?, status = 'open' WHERE id = ?",
                     (new_due_date, task_id))
    conn.commit()
    conn.close()


def get_overdue_tasks():
    """Gibt überfällige offene Tasks zurück."""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    rows = conn.execute(
        "SELECT t.*, p.name as project_name FROM tasks t LEFT JOIN projects p ON t.project_id = p.id "
        "WHERE t.status = 'open' AND t.due_date IS NOT NULL AND t.due_date < ? "
        "ORDER BY t.due_date ASC", (today,)
    ).fetchall()
    conn.close()
    return rows


def find_task(query):
    """Sucht einen Task nach Titel (LIKE-Suche)."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM tasks WHERE title LIKE ? AND status != 'done' ORDER BY created_at DESC LIMIT 1",
        ("%" + query + "%",)
    ).fetchone()
    conn.close()
    return row


def get_tasks_completed_today():
    """Gibt heute erledigte Tasks zurück."""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE completed_at LIKE ? || '%'", (today,)
    ).fetchall()
    conn.close()
    return rows


def format_tasks(tasks):
    """Formatiert Tasks als lesbaren Text."""
    if not tasks:
        return "Keine Tasks."
    lines = []
    for t in tasks:
        line = "  [" + str(t["id"]) + "] "
        if t["priority"] in ("urgent", "high"):
            line += "!" + t["priority"].upper() + " "
        proj = t["project_name"] if "project_name" in t.keys() and t["project_name"] else ""
        if proj:
            line += "[" + proj + "] "
        line += t["title"]
        if t["due_date"]:
            line += " (bis " + t["due_date"] + ")"
        lines.append(line)
    return "\n".join(lines)
