"""Gewohnheiten-Tracking — CRUD, Logging, Streak-Berechnung."""

from datetime import datetime, timedelta
from database import get_db


def list_habits(active_only=True):
    """Gibt alle Habits zurück."""
    conn = get_db()
    sql = "SELECT * FROM habits"
    if active_only:
        sql += " WHERE active = 1"
    rows = conn.execute(sql).fetchall()
    conn.close()
    return rows


def create_habit(name, category=None, target_frequency="daily", target_description=None):
    """Erstellt einen neuen Habit."""
    conn = get_db()
    conn.execute(
        "INSERT INTO habits (name, category, target_frequency, target_description) VALUES (?, ?, ?, ?)",
        (name, category, target_frequency, target_description)
    )
    conn.commit()
    conn.close()


def log_habit(habit_id, completed=True, notes=None):
    """Loggt einen Habit für heute."""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO habit_log (habit_id, date, completed, notes) VALUES (?, ?, ?, ?)",
        (habit_id, today, 1 if completed else 0, notes)
    )
    conn.commit()
    conn.close()


def get_habit_stats(habit_id, days=14):
    """Gibt Stats für einen Habit zurück: total, completed, streak, rate."""
    conn = get_db()
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT date, completed FROM habit_log WHERE habit_id = ? AND date >= ? ORDER BY date DESC",
        (habit_id, since)
    ).fetchall()
    conn.close()

    total = days
    completed = sum(1 for r in rows if r["completed"])
    rate = round(completed / total * 100) if total > 0 else 0

    # Streak berechnen (aufeinanderfolgende Tage)
    streak = 0
    check = datetime.now().date()
    dates_done = {r["date"] for r in rows if r["completed"]}
    for i in range(days):
        d = (check - timedelta(days=i)).strftime("%Y-%m-%d")
        if d in dates_done:
            streak += 1
        else:
            break

    return {"total": total, "completed": completed, "streak": streak, "rate": rate}


def get_today_habits():
    """Gibt Habits für heute mit Log-Status zurück."""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    rows = conn.execute(
        "SELECT h.*, hl.completed as done_today FROM habits h "
        "LEFT JOIN habit_log hl ON h.id = hl.habit_id AND hl.date = ? "
        "WHERE h.active = 1", (today,)
    ).fetchall()
    conn.close()
    return rows


def find_habit(query):
    """Sucht einen Habit nach Name."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM habits WHERE name LIKE ? AND active = 1", ("%" + query + "%",)
    ).fetchone()
    conn.close()
    return row
