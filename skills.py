"""Skill-Registry — Prompt-Lookup, Matching, Nutzungszählung."""

from database import get_db


def find_matching_skill(user_input):
    """Sucht einen Skill dessen Keywords zum Input passen."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM skills WHERE enabled = 1 AND trigger_keywords IS NOT NULL"
    ).fetchall()
    conn.close()

    lower = user_input.lower()
    best = None
    best_score = 0

    for skill in rows:
        keywords = [k.strip() for k in (skill["trigger_keywords"] or "").split(",")]
        score = sum(1 for kw in keywords if kw and kw in lower)
        if score > best_score:
            best = skill
            best_score = score

    return best if best_score >= 1 else None


def get_skill_prompt(skill_id):
    """Gibt den Prompt eines Skills zurück."""
    conn = get_db()
    row = conn.execute("SELECT prompt FROM skills WHERE id = ?", (skill_id,)).fetchone()
    conn.close()
    return row["prompt"] if row else None


def increment_usage(skill_id):
    """Zählt die Nutzung eines Skills hoch."""
    conn = get_db()
    conn.execute("UPDATE skills SET usage_count = usage_count + 1 WHERE id = ?", (skill_id,))
    conn.commit()
    conn.close()


def list_skills(category=None):
    """Gibt verfügbare Skills zurück."""
    conn = get_db()
    if category:
        rows = conn.execute(
            "SELECT name, category, usage_count FROM skills WHERE enabled = 1 AND category = ? ORDER BY usage_count DESC",
            (category,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT name, category, usage_count FROM skills WHERE enabled = 1 ORDER BY category, name"
        ).fetchall()
    conn.close()
    return rows
