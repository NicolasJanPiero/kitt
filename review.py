"""Tages- und Wochenrückblick."""

from datetime import datetime, timedelta
from database import get_db
from tasks import list_tasks, get_tasks_completed_today


def generate_day_review():
    """Erstellt einen Tagesrückblick."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = ["Tagesrueckblick " + datetime.now().strftime("%A, %d.%m.%Y"), ""]

    # Erledigte Tasks
    done = get_tasks_completed_today()
    if done:
        lines.append("Erledigt (" + str(len(done)) + "):")
        for t in done:
            lines.append("  + " + t["title"])
    else:
        lines.append("Erledigt: nichts")
    lines.append("")

    # Verschobene Tasks (heute deferred)
    conn = get_db()
    deferred = conn.execute(
        "SELECT * FROM tasks WHERE status = 'deferred' AND created_at LIKE ? || '%'", (today,)
    ).fetchall()
    conn.close()
    if deferred:
        lines.append("Verschoben (" + str(len(deferred)) + "):")
        for t in deferred:
            lines.append("  > " + t["title"])
        lines.append("")

    # Offene Tasks
    open_tasks = list_tasks(status="open", limit=5)
    if open_tasks:
        lines.append("Noch offen (" + str(len(open_tasks)) + "):")
        for t in open_tasks:
            lines.append("  - " + t["title"])
        lines.append("")

    # Score
    total = len(done) + len(open_tasks) + len(deferred)
    score = str(len(done)) + "/" + str(total) if total > 0 else "0/0"
    lines.append("Score: " + score)

    return "\n".join(lines)


def generate_week_review():
    """Erstellt einen Wochenrückblick."""
    conn = get_db()
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    lines = ["Wochenrueckblick KW " + datetime.now().strftime("%V"), ""]

    # Tasks diese Woche
    created = conn.execute(
        "SELECT count(*) as c FROM tasks WHERE created_at >= ?", (week_ago,)
    ).fetchone()["c"]
    done = conn.execute(
        "SELECT count(*) as c FROM tasks WHERE status='done' AND completed_at >= ?", (week_ago,)
    ).fetchone()["c"]
    deferred = conn.execute(
        "SELECT count(*) as c FROM tasks WHERE status='deferred' AND created_at >= ?", (week_ago,)
    ).fetchone()["c"]

    lines.append("Tasks:")
    lines.append("  Erstellt: " + str(created) + " | Erledigt: " + str(done) + " | Verschoben: " + str(deferred))
    rate = str(round(done / created * 100)) + "%" if created > 0 else "–"
    lines.append("  Erledigungsrate: " + rate)
    lines.append("")

    # Projekte
    projects = conn.execute(
        "SELECT name, next_action FROM projects WHERE status='active' ORDER BY priority DESC"
    ).fetchall()
    if projects:
        lines.append("Projekte (" + str(len(projects)) + " aktiv):")
        for p in projects:
            lines.append("  " + p["name"] + " → " + (p["next_action"] or "kein naechster Schritt"))
        lines.append("")

    # Habits (wenn vorhanden)
    habits = conn.execute(
        "SELECT h.name, count(hl.id) as done_count FROM habits h "
        "LEFT JOIN habit_log hl ON h.id = hl.habit_id AND hl.date >= ? AND hl.completed = 1 "
        "WHERE h.active = 1 GROUP BY h.id", (week_ago,)
    ).fetchall()
    if habits:
        lines.append("Habits:")
        for h in habits:
            lines.append("  " + h["name"] + ": " + str(h["done_count"]) + "x diese Woche")

    conn.close()
    return "\n".join(lines)
