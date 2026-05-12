"""Tages- und Wochenplanung — Kalender + Tasks + Habits."""

from datetime import datetime
from calendar_tool import get_events_today
from heartbeat import parse_icalbuddy_output, fetch_calendar_local
from tasks import list_tasks, get_overdue_tasks
from projects import list_projects


def generate_day_plan():
    """Erstellt eine strukturierte Tagesübersicht."""
    now = datetime.now()
    lines = ["Tagesplan " + now.strftime("%A, %d.%m.%Y"), ""]

    # Kalender
    raw = fetch_calendar_local()
    events = parse_icalbuddy_output(raw)
    if events:
        lines.append("Termine:")
        for e in events:
            line = "  " + e["time"] + "  " + e["subject"]
            if e["attendees"]:
                line += " (" + e["attendees"] + ")"
            lines.append(line)
    else:
        lines.append("Termine: keine")
    lines.append("")

    # Überfällige Tasks
    overdue = get_overdue_tasks()
    if overdue:
        lines.append("Ueberfaellig:")
        for t in overdue:
            proj = ""
            if "project_name" in t.keys() and t["project_name"]:
                proj = "[" + t["project_name"] + "] "
            lines.append("  ! " + proj + t["title"] + " (seit " + t["due_date"] + ")")
        lines.append("")

    # Offene Tasks nach Priorität
    tasks = list_tasks(status="open", limit=10)
    if tasks:
        lines.append("Tasks (offen):")
        for t in tasks:
            prio = ""
            if t["priority"] in ("urgent", "high"):
                prio = "!" + t["priority"].upper() + " "
            proj = ""
            if "project_name" in t.keys() and t["project_name"]:
                proj = "[" + t["project_name"] + "] "
            lines.append("  " + prio + proj + t["title"])
    else:
        lines.append("Tasks: keine offenen")
    lines.append("")

    # Projekte mit Next Actions
    projects = list_projects()
    if projects:
        active_with_action = [p for p in projects if p["next_action"]]
        if active_with_action:
            lines.append("Projekt-Next-Actions:")
            for p in active_with_action[:5]:
                lines.append("  " + p["name"] + " → " + p["next_action"])
        lines.append("")

    # Habits (wenn vorhanden)
    try:
        from database import get_db
        conn = get_db()
        habits = conn.execute("SELECT name, target_frequency FROM habits WHERE active = 1").fetchall()
        conn.close()
        if habits:
            lines.append("Habits heute:")
            for h in habits:
                lines.append("  [ ] " + h["name"] + " (" + (h["target_frequency"] or "") + ")")
            lines.append("")
    except Exception:
        pass

    return "\n".join(lines)


def generate_week_plan():
    """Erstellt eine Wochenübersicht."""
    lines = ["Wochenplan KW " + datetime.now().strftime("%V, %Y"), ""]

    projects = list_projects()
    if projects:
        lines.append("Aktive Projekte (" + str(len(projects)) + "):")
        for p in projects:
            line = "  " + p["name"] + " (Prio " + str(p["priority"]) + ")"
            if p["next_action"]:
                line += " → " + p["next_action"]
            lines.append(line)
        lines.append("")

    tasks = list_tasks(status="open", limit=20)
    if tasks:
        lines.append("Offene Tasks (" + str(len(tasks)) + "):")
        for t in tasks:
            proj = ""
            if "project_name" in t.keys() and t["project_name"]:
                proj = "[" + t["project_name"] + "] "
            lines.append("  " + proj + t["title"])
        lines.append("")

    overdue = get_overdue_tasks()
    if overdue:
        lines.append("Ueberfaellig (" + str(len(overdue)) + "):")
        for t in overdue:
            lines.append("  ! " + t["title"] + " (seit " + t["due_date"] + ")")

    return "\n".join(lines)
