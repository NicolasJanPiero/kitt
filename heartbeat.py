"""Reactive Heartbeat — Vorschläge beim Start, KEIN Hintergrund-Scheduler."""

import json
import os
import subprocess
from datetime import datetime
from config import WORKSPACE

# Heartbeat-Regeln (hardcoded, auditierbar)
HEARTBEAT_RULES = [
    {
        "name": "Kalender checken",
        "schedule": "daily",
        "command": None,
        "simai_task": None,
        "description": "Heutige Termine aus macOS Kalender",
        "handler": "calendar",
    },
    {
        "name": "Downloads aufräumen",
        "schedule": "daily",
        "command": "ls ~/agent-workspace/ | head -20",
        "simai_task": None,
        "description": "Workspace-Inhalt prüfen und aufräumen",
        "handler": None,
    },
    {
        "name": "Wochenrückblick",
        "schedule": "weekly_monday",
        "command": None,
        "simai_task": "Erstelle einen Wochenrückblick der laufenden Projekte",
        "description": "Projektübersicht von sim.ai-claw holen",
        "handler": None,
    },
    {
        "name": "Log-Review",
        "schedule": "weekly_friday",
        "command": "wc -l ~/agent-workspace/logs/*.log 2>/dev/null | tail -5",
        "simai_task": None,
        "description": "Agent-Logs der Woche zusammenfassen",
        "handler": None,
    },
]


def get_due_suggestions():
    """Gibt die heute fälligen Heartbeat-Vorschläge zurück."""
    today = datetime.now().strftime("%A").lower()

    due = []
    for rule in HEARTBEAT_RULES:
        if rule["schedule"] == "daily":
            due.append(rule)
        elif rule["schedule"] == "weekly_monday" and today == "monday":
            due.append(rule)
        elif rule["schedule"] == "weekly_friday" and today == "friday":
            due.append(rule)
    return due


def show_heartbeat():
    """Zeigt fällige Vorschläge. Gibt Liste zurück oder None."""
    suggestions = get_due_suggestions()
    if not suggestions:
        return None

    print("\n--- Heartbeat-Vorschlaege fuer heute:")
    for i, s in enumerate(suggestions, 1):
        print("  " + str(i) + ". " + s["name"] + " -- " + s["description"])

    print("\nAusfuehren? (Nummer, 'alle', oder 'skip')")
    return suggestions


def fetch_calendar_local():
    """Liest heutige Termine direkt aus macOS Calendar via icalBuddy."""
    import re
    try:
        result = subprocess.run(
            ["icalBuddy", "-nc", "-nrd", "-npn", "-nc",
             "-iep", "datetime,title,attendees",
             "-po", "datetime,title,attendees",
             "-ps", "|;|",
             "-b", "",
             "eventsToday"],
            capture_output=True, text=True, timeout=10,
            env=dict(os.environ, NO_COLOR="1", TERM="dumb")
        )
        # ANSI-Codes entfernen
        output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
        return output.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def parse_icalbuddy_output(raw):
    """Parst icalBuddy Output zu Event-Liste."""
    events = []
    if not raw:
        return events
    for line in raw.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split(";")
        if len(parts) >= 2:
            time = parts[0].strip()
            subject = parts[1].strip()
            attendees = parts[2].strip() if len(parts) >= 3 else ""
        else:
            # Kein Separator = Ganztags-Event ohne Uhrzeit
            time = "ganztags"
            subject = parts[0].strip()
            attendees = ""
        if subject:
            events.append({"time": time, "subject": subject, "attendees": attendees})
    return events


def handle_calendar_response(result):
    """Liest Kalender lokal via icalBuddy und bietet Tagesliste an."""
    raw = fetch_calendar_local()

    if not raw:
        print("\n  Keine Termine heute.")
        return

    events = parse_icalbuddy_output(raw)

    if not events:
        # Rohe Ausgabe zeigen falls Parsing fehlschlaegt
        print("\n  Termine heute:")
        for line in raw.split("\n"):
            print("    " + line)
        return

    # Termine formatiert anzeigen
    print("\n  Termine heute:")
    print("  " + "-" * 40)
    for ev in events:
        line = "  " + ev["time"] + "  " + ev["subject"]
        if ev["attendees"]:
            line += " (" + ev["attendees"] + ")"
        print(line)
    print("  " + "-" * 40)
    print("  " + str(len(events)) + " Termine\n")

    # Tagesliste anbieten
    try:
        answer = input("  Tagesliste erstellen? [Y/n] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return

    if answer in ("", "y", "yes", "j", "ja"):
        create_todo_file(events)


def create_todo_file(events):
    """Erstellt ~/agent-workspace/todo-YYYY-MM-DD.md aus Terminen."""
    today = datetime.now().strftime("%Y-%m-%d")
    filename = os.path.join(WORKSPACE, "todo-" + today + ".md")

    lines = ["# Tagesliste " + today, ""]
    for ev in events:
        line = "- [ ] " + ev["time"] + " " + ev["subject"]
        if ev["attendees"]:
            line += " (" + ev["attendees"] + ")"
        lines.append(line)

    lines.append("")
    lines.append("## Notizen")
    lines.append("")

    with open(filename, "w") as f:
        f.write("\n".join(lines))

    print("  Erstellt: " + filename)
