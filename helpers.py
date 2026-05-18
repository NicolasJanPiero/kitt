"""Hilfsfunktionen — Parsing, Prompts, Klassifizierung."""

import os
import re
from config import SIMAI_KEYWORDS, PERSONAL_KEYWORDS, SOUL_PATH
from llm import CLASS_PERSONAL, CLASS_WORK
from memory import get_context_for_prompt


def show_help():
    print("\nBefehle:")
    print("  projekte                -- Alle Projekte")
    print("  projekt <name>          -- Projekt-Details")
    print("  neues projekt: <name>   -- Projekt erstellen")
    print("  tasks                   -- Offene Tasks")
    print("  neuer task: <titel>     -- Task erstellen")
    print("  erledigt <titel>        -- Task abschliessen")
    print("  plan                    -- Tagesplan")
    print("  wochenplan              -- Wochenplan")
    print("  review                  -- Tagesrueckblick")
    print("  wochenrueckblick        -- Wochenrueckblick")
    print("  habits                  -- Habits mit Stats")
    print("  training gemacht        -- Habit loggen")
    print("  stats                   -- Fortschritt")
    print("  merk dir: <fakt>        -- Fakt speichern")
    print("  was weisst du ueber X   -- Memory durchsuchen")
    print("  skills                  -- Verfuegbare Skills")
    print("  heartbeat               -- Heartbeat-Vorschlaege")
    print("  bridge status           -- sim.ai Verbindung")
    print("  log                     -- Letzte 20 Aktionen")
    print("  exit/quit               -- Beenden")
    print("  (alles andere)          -- Nachricht an KITT\n")


def show_log(log_dir):
    """Zeigt die letzten 20 Log-Eintraege."""
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    logfile = os.path.join(log_dir, today + ".log")
    if not os.path.exists(logfile):
        print("(Heute noch keine Logs)")
        return
    with open(logfile, "r") as f:
        lines = f.readlines()
    for line in lines[-20:]:
        print("  " + line.rstrip())


def parse_command(response):
    """Extrahiert BEFEHL: ... aus der Agent-Antwort."""
    match = re.search(r"BEFEHL:\s*`?(.+?)`?(?:\n|$)", response)
    return match.group(1).strip() if match else None


def parse_calendar_event(response):
    """Extrahiert TERMIN: titel | datum | uhrzeit | dauer aus der Agent-Antwort."""
    match = re.search(r"TERMIN:\s*(.+?)(?:\n|$)", response)
    if not match:
        return None
    parts = [p.strip() for p in match.group(1).split("|")]
    if len(parts) < 3:
        return None
    title = parts[0]
    date_str = parts[1]
    time_str = parts[2]
    duration = 30
    if len(parts) >= 4:
        dur_match = re.search(r'\d+', parts[3])
        if dur_match:
            duration = int(dur_match.group())
    from datetime import datetime as dt
    try:
        start = dt.strptime(date_str + " " + time_str, "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            start = dt.strptime(date_str + " " + time_str, "%d.%m.%Y %H:%M")
        except ValueError:
            return None
    return {"title": title, "start": start, "duration": duration}


def confirm(prompt):
    """Fragt den User nach Bestaetigung."""
    try:
        answer = input(prompt + " [Y/n] ").strip().lower()
        return answer in ("", "y", "yes", "j", "ja")
    except (EOFError, KeyboardInterrupt):
        return False


def classify_input(text):
    """Bestimmt die Datenklasse eines User-Inputs fuer LLM-Routing."""
    lower = text.lower()
    if any(kw in lower for kw in PERSONAL_KEYWORDS):
        return CLASS_PERSONAL
    return CLASS_WORK


def contains_simai_keyword(text):
    """Prueft ob der Text sim.ai-relevante Keywords enthaelt."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in SIMAI_KEYWORDS)


def load_system_prompt():
    """Laedt den System-Prompt aus DB (personality_xml) + Kontext."""
    prompt = ""
    try:
        from database import get_db
        conn = get_db()
        row = conn.execute("SELECT value FROM soul WHERE key='personality_xml'").fetchone()
        conn.close()
        if row and row["value"]:
            prompt = row["value"]
    except Exception:
        pass

    if not prompt:
        try:
            with open(SOUL_PATH) as f:
                prompt = f.read()
        except FileNotFoundError:
            prompt = "Du bist KITT, ein hilfreicher Assistent. Antworte kurz auf Deutsch."

    try:
        context = get_context_for_prompt()
        if context:
            prompt += "\n\n<aktueller_kontext>\n" + context + "\n</aktueller_kontext>"
    except Exception:
        pass

    return prompt
