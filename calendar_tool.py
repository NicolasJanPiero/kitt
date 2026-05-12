"""Kalender-Tool — Termine lesen und erstellen via macOS Calendar (synct zu Outlook)."""

import subprocess
import os
import re
from datetime import datetime, timedelta
from sandbox import log_action

# Standard-Kalender (Exchange/Outlook)
DEFAULT_CALENDAR = "Kalender"


def get_events_today():
    """Liest heutige Termine via icalBuddy."""
    try:
        result = subprocess.run(
            ["icalBuddy", "-nc", "-nrd", "-npn",
             "-iep", "datetime,title,attendees",
             "-po", "datetime,title,attendees",
             "-ps", "|;|",
             "-b", "",
             "eventsToday"],
            capture_output=True, text=True, timeout=10,
            env=dict(os.environ, NO_COLOR="1", TERM="dumb")
        )
        output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
        return output.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def create_event(title, start_dt, duration_minutes=30, calendar=None):
    """Erstellt einen Termin via AppleScript. Gibt (success, message) zurück."""
    cal = calendar or DEFAULT_CALENDAR
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    # AppleScript mit relativem Datum (sprachunabhaengig)
    # Berechne Sekunden ab jetzt bis Start/Ende
    now = datetime.now()
    start_offset = int((start_dt - now).total_seconds())
    duration_secs = duration_minutes * 60

    script = (
        'tell application "Calendar"\n'
        '    tell calendar "' + cal + '"\n'
        '        set startDate to (current date) + ' + str(start_offset) + '\n'
        '        set endDate to startDate + ' + str(duration_secs) + '\n'
        '        make new event with properties '
        '{summary:"' + title.replace('"', '\\"') + '", '
        'start date:startDate, end date:endDate}\n'
        '    end tell\n'
        'end tell'
    )

    log_action("CALENDAR_CREATE", title + " @ " + start_dt.strftime("%d.%m.%Y %H:%M") + " (" + str(duration_minutes) + "min)")

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            log_action("CALENDAR_OK", "Termin erstellt: " + title)
            return True, "Termin erstellt: " + title + " am " + start_dt.strftime("%d.%m.%Y %H:%M") + " (" + str(duration_minutes) + " Min.)"
        else:
            err = result.stderr.strip()
            log_action("CALENDAR_ERROR", err)
            return False, "Fehler: " + err
    except subprocess.TimeoutExpired:
        return False, "Fehler: Timeout beim Erstellen"


def parse_event_request(text):
    """Versucht Termin-Details aus Text zu extrahieren. Gibt dict oder None zurück."""
    # Wird vom Ollama-Agent gemacht — hier nur als Fallback
    return None
