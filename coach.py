"""Coaching — Motivations-Nudges, Pattern-Erkennung, Beobachtungen."""

from datetime import datetime, timedelta
from database import get_db
from memory import save_memory


def get_nudge():
    """Gibt den relevantesten Coaching-Nudge zurück (oder None)."""
    conn = get_db()

    # Max 1 Nudge pro Session
    row = conn.execute("SELECT value FROM soul WHERE key='last_nudge_session'").fetchone()
    current_session = None
    try:
        from agent import SESSION_ID
        current_session = SESSION_ID
    except ImportError:
        pass
    if row and current_session and row["value"] == current_session:
        conn.close()
        return None

    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    nudge = None

    # Pattern 1: Tasks die oft verschoben wurden
    deferred = conn.execute(
        "SELECT title, count(*) as c FROM tasks WHERE status = 'deferred' "
        "GROUP BY title HAVING c >= 2 LIMIT 1"
    ).fetchone()
    if deferred:
        nudge = "'" + deferred["title"] + "' wurde " + str(deferred["c"]) + "x verschoben. Zu gross? Aufteilen?"

    # Pattern 2: Habit-Frequenz unter Ziel
    if not nudge:
        habits = conn.execute(
            "SELECT h.name, h.target_frequency, count(hl.id) as done "
            "FROM habits h LEFT JOIN habit_log hl ON h.id = hl.habit_id "
            "AND hl.date >= ? AND hl.completed = 1 "
            "WHERE h.active = 1 GROUP BY h.id", (week_ago,)
        ).fetchall()
        for h in habits:
            target = 7 if h["target_frequency"] == "daily" else 3 if "3x" in (h["target_frequency"] or "") else 2
            if h["done"] < target // 2 and target > 1:
                nudge = h["name"] + ": " + str(h["done"]) + "x in 7 Tagen (Ziel: " + str(target) + "). Heute einplanen?"
                break

    # Pattern 3: Gute Woche
    if not nudge:
        done_count = conn.execute(
            "SELECT count(*) as c FROM tasks WHERE status='done' AND completed_at >= ?", (week_ago,)
        ).fetchone()["c"]
        total = conn.execute(
            "SELECT count(*) as c FROM tasks WHERE created_at >= ?", (week_ago,)
        ).fetchone()["c"]
        if total > 3 and done_count / total > 0.8:
            nudge = str(done_count) + "/" + str(total) + " Tasks erledigt diese Woche. Starke Leistung."

    conn.close()

    # Nudge-Session merken
    if nudge and current_session:
        c = get_db()
        c.execute("INSERT OR REPLACE INTO soul (key, value) VALUES ('last_nudge_session', ?)", (current_session,))
        c.commit()
        c.close()

    return nudge


def log_observation(observation):
    """Speichert eine Agent-Beobachtung."""
    save_memory("observation", observation, source="agent", importance=6)
