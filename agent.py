#!/usr/bin/env python3
"""KITT v1.0 — Terminal + Signal, Kalender, sim.ai-Bridge, Hybrid-LLM."""

import os
import re
import sys
import time
import uuid
from config import WORKSPACE, LOG_DIR, SIMAI_KEYWORDS, SIMAI_WEBHOOK_URL
from database import init_db, log_to_db
from llm import chat, CLASS_PERSONAL, CLASS_WORK, CLASS_SKILL
from memory import save_memory, search_memory, get_recent_memories, get_context_for_prompt
from onboarding import is_onboarding_needed, run_onboarding
from projects import list_projects, get_project, create_project, format_projects
from tasks import list_tasks, create_task, complete_task, find_task, format_tasks, get_overdue_tasks
from planner import generate_day_plan, generate_week_plan
from review import generate_day_review, generate_week_review
from habits import list_habits, find_habit, log_habit, get_habit_stats, get_today_habits
from coach import get_nudge
from skills import find_matching_skill, get_skill_prompt, increment_usage, list_skills
from knowledge import auto_extract_entities, create_entity
from sandbox import execute_command, is_safe_path, log_action
from simai_bridge import delegate_to_simai, check_bridge_status, is_bridge_configured
from heartbeat import show_heartbeat, handle_calendar_response
from calendar_tool import create_event
from signal_channel import send_message, receive_messages

SESSION_ID = str(uuid.uuid4())[:8]


def setup(channel="terminal"):
    """Erstellt Workspace, Log-Verzeichnis, initialisiert DB, startet Session."""
    os.makedirs(WORKSPACE, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    is_new = init_db()
    if is_new:
        print("Datenbank erstellt: kitt.db")
    # Session in DB registrieren
    try:
        from database import get_db
        conn = get_db()
        conn.execute("INSERT OR IGNORE INTO sessions (id, channel) VALUES (?, ?)", (SESSION_ID, channel))
        conn.commit()
        conn.close()
    except Exception:
        pass


def show_help():
    print("\nBefehle:")
    print("  projekte                — Alle Projekte")
    print("  projekt <name>          — Projekt-Details")
    print("  neues projekt: <name>   — Projekt erstellen")
    print("  tasks                   — Offene Tasks")
    print("  neuer task: <titel>     — Task erstellen")
    print("  erledigt <titel>        — Task abschliessen")
    print("  plan                    — Tagesplan")
    print("  wochenplan              — Wochenplan")
    print("  review                  — Tagesrueckblick")
    print("  wochenrueckblick        — Wochenrueckblick")
    print("  habits                  — Habits mit Stats")
    print("  training gemacht        — Habit loggen")
    print("  stats                   — Fortschritt")
    print("  merk dir: <fakt>        — Fakt speichern")
    print("  was weisst du ueber X   — Memory durchsuchen")
    print("  heartbeat               — Heartbeat-Vorschlaege")
    print("  exit/quit               — Beenden")
    print("  (alles andere)          — Nachricht an KITT\n")


def show_log():
    """Zeigt die letzten 20 Log-Einträge."""
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    logfile = os.path.join(LOG_DIR, today + ".log")
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
    if match:
        return match.group(1).strip()
    return None


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
    # Dauer extrahieren — nur die Zahl nehmen
    duration = 30
    if len(parts) >= 4:
        dur_match = re.search(r'\d+', parts[3])
        if dur_match:
            duration = int(dur_match.group())

    # Datum+Uhrzeit parsen
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
    """Fragt den User nach Bestätigung."""
    try:
        answer = input(prompt + " [Y/n] ").strip().lower()
        return answer in ("", "y", "yes", "j", "ja")
    except (EOFError, KeyboardInterrupt):
        return False


def classify_input(text):
    """Bestimmt die Datenklasse eines User-Inputs fuer LLM-Routing."""
    lower = text.lower()
    personal_kw = ["habit", "training", "gym", "schlaf", "gesundheit", "meditation",
                   "wasser", "sport", "ernaehrung", "gewohnheit", "feierabend"]
    for kw in personal_kw:
        if kw in lower:
            return CLASS_PERSONAL
    return CLASS_WORK


def _load_system_prompt():
    """Lädt den System-Prompt aus DB (personality_xml) + Kontext (Projekte, Memories)."""
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
        from config import SOUL_PATH
        try:
            with open(SOUL_PATH) as f:
                prompt = f.read()
        except FileNotFoundError:
            prompt = "Du bist KITT, ein hilfreicher Assistent. Antworte kurz auf Deutsch."

    # DB-Kontext anfügen
    try:
        context = get_context_for_prompt()
        if context:
            prompt += "\n\n<aktueller_kontext>\n" + context + "\n</aktueller_kontext>"
    except Exception:
        pass

    return prompt


def contains_simai_keyword(text):
    """Prüft ob der Text sim.ai-relevante Keywords enthält."""
    text_lower = text.lower()
    for keyword in SIMAI_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


def handle_heartbeat_choice(suggestions):
    """Verarbeitet die Heartbeat-Auswahl."""
    try:
        choice = input("> ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return

    if choice == "skip" or not choice:
        print("Ok, uebersprungen.\n")
        return

    if choice == "alle":
        for s in suggestions:
            execute_heartbeat_item(s)
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(suggestions):
            execute_heartbeat_item(suggestions[idx])
        else:
            print("Ungueltige Nummer.\n")
    except ValueError:
        print("Ok, uebersprungen.\n")


def execute_heartbeat_item(item):
    """Führt einen Heartbeat-Vorschlag aus (mit Bestätigung)."""
    print("\n  " + item["name"] + ": " + item["description"])

    if item.get("handler") == "calendar":
        # Kalender direkt vom dedizierten Workflow abrufen
        if confirm("  Outlook-Kalender abrufen?"):
            handle_calendar_response(None)
        else:
            print("  Uebersprungen.\n")
    elif item.get("simai_task"):
        if not is_bridge_configured():
            print("  -> sim.ai Bridge nicht konfiguriert, uebersprungen.\n")
            return
        if confirm("  An sim.ai senden?"):
            result = delegate_to_simai(item["simai_task"])
            print("  sim.ai: " + str(result) + "\n")
        else:
            print("  Uebersprungen.\n")
    elif item.get("command"):
        print("  Befehl: " + item["command"])
        if confirm("  Ausfuehren?"):
            output, rc = execute_command(item["command"])
            print("  " + output + "\n")
        else:
            print("  Uebersprungen.\n")
    else:
        print("  (Kein automatischer Befehl, manuell erledigen)\n")


def main():
    setup()
    log_action("START", "KITT v1.0 gestartet")

    # Onboarding prüfen
    if is_onboarding_needed():
        run_onboarding()

    print("KITT v1.0 — Reactive Mode (Session " + SESSION_ID + ")")
    if is_bridge_configured():
        print("sim.ai Bridge: aktiv")
    print("Was soll ich tun? (help fuer Befehle)\n")

    # Reactive Heartbeat beim Start
    suggestions = show_heartbeat()
    if suggestions:
        handle_heartbeat_choice(suggestions)

    # Morgen-Nudge
    nudge = get_nudge()
    if nudge:
        print("KITT: " + nudge + "\n")

    history = []

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTschuess.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("Tschuess.")
            log_action("EXIT", "Agent beendet")
            break

        if user_input.lower() == "log":
            show_log()
            continue

        if user_input.lower() == "help":
            show_help()
            continue

        if user_input.lower() == "heartbeat":
            suggestions = show_heartbeat()
            if suggestions:
                handle_heartbeat_choice(suggestions)
            else:
                print("(Keine Vorschlaege fuer heute)")
            continue

        if user_input.lower() == "bridge status":
            print(check_bridge_status())
            continue

        # Memory-Befehle
        lower = user_input.lower()
        if lower.startswith("merk dir") or lower.startswith("merke dir") or lower.startswith("remember"):
            fact = user_input.split(":", 1)[1].strip() if ":" in user_input else user_input.split(" ", 2)[-1]
            save_memory("fact", fact, source="user", importance=7, session_id=SESSION_ID)
            print("Gemerkt: " + fact + "\n")
            log_action("MEMORY_SAVE", fact)
            continue

        if lower.startswith("was weisst du") or lower.startswith("was weißt du"):
            query = user_input.split("ueber")[-1].split("über")[-1].strip().rstrip("?")
            if not query or query == user_input or query in ("mich", "mir", "meine"):
                query = ""
            results = search_memory(query) if query else get_recent_memories(limit=10)
            if results:
                print("\nDas weiss ich:")
                for r in results[:10]:
                    print("  [" + r["type"] + "] " + r["content"][:100])
                print("")
            else:
                print("Dazu habe ich noch nichts gespeichert.\n")
            continue

        # Produktivitäts-Befehle
        if lower == "projekte":
            print("\n" + format_projects(list_projects()) + "\n")
            continue

        if lower.startswith("projekt "):
            name = user_input[8:].strip()
            p = get_project(name)
            if p:
                print("\n  " + p["name"] + " (Prio " + str(p["priority"]) + ", " + p["status"] + ")")
                if p["description"]:
                    print("  " + p["description"])
                if p["next_action"]:
                    print("  Next: " + p["next_action"])
                if p["notes"]:
                    print("  Notizen:\n  " + p["notes"].replace("\n", "\n  "))
                print("")
            else:
                print("Projekt nicht gefunden.\n")
            continue

        if lower.startswith("neues projekt"):
            name = user_input.split(":", 1)[1].strip() if ":" in user_input else user_input[14:].strip()
            if name:
                create_project(name)
                print("Projekt erstellt: " + name + "\n")
            else:
                print("Nutzung: neues projekt: Name\n")
            continue

        if lower == "tasks" or lower == "aufgaben":
            print("\n" + format_tasks(list_tasks()) + "\n")
            continue

        if lower.startswith("neuer task") or lower.startswith("neue aufgabe"):
            title = user_input.split(":", 1)[1].strip() if ":" in user_input else user_input.split(" ", 2)[-1]
            if title and title not in ("task", "aufgabe"):
                create_task(title)
                print("Task erstellt: " + title + "\n")
            else:
                print("Nutzung: neuer task: Titel\n")
            continue

        if lower.startswith("erledigt"):
            query = user_input[8:].strip().lstrip(":").strip()
            if query:
                t = find_task(query)
                if t:
                    complete_task(t["id"])
                    print("Erledigt: " + t["title"] + "\n")
                else:
                    print("Task nicht gefunden: " + query + "\n")
            else:
                print("Nutzung: erledigt Taskname\n")
            continue

        if lower in ("plan", "tagesplan"):
            print("\n" + generate_day_plan() + "\n")
            continue

        if lower in ("wochenplan", "woche"):
            print("\n" + generate_week_plan() + "\n")
            continue

        if lower in ("review", "rueckblick", "tagesrueckblick"):
            print("\n" + generate_day_review() + "\n")
            continue

        if lower in ("wochenrueckblick", "wochenreview"):
            print("\n" + generate_week_review() + "\n")
            continue

        if lower == "habits" or lower == "gewohnheiten":
            habits = get_today_habits()
            if habits:
                print("\nHabits heute:")
                for h in habits:
                    status = "[x]" if h["done_today"] else "[ ]"
                    stats = get_habit_stats(h["id"])
                    print("  " + status + " " + h["name"] + " (Streak: " + str(stats["streak"]) + "d, Rate: " + str(stats["rate"]) + "%)")
                print("")
            else:
                print("Keine Habits angelegt. Starte Onboarding Session 3.\n")
            continue

        if lower.startswith("training") or lower.startswith("habit "):
            # "training gemacht" oder "habit Meditation erledigt"
            query = lower.replace("training", "training").replace("gemacht", "").replace("erledigt", "").strip()
            if "habit " in lower:
                query = lower.split("habit ", 1)[1].replace("erledigt", "").replace("gemacht", "").strip()
            h = find_habit(query) if query else find_habit("training")
            if h:
                log_habit(h["id"])
                stats = get_habit_stats(h["id"])
                print(h["name"] + " geloggt. Streak: " + str(stats["streak"]) + " Tage.\n")
            else:
                print("Habit nicht gefunden.\n")
            continue

        if lower == "skills":
            sk = list_skills()
            if sk:
                print("\nVerfuegbare Skills (" + str(len(sk)) + "):")
                current_cat = ""
                for s in sk:
                    if s["category"] != current_cat:
                        current_cat = s["category"]
                        print("  " + current_cat.upper() + ":")
                    print("    " + s["name"] + " (" + str(s["usage_count"]) + "x genutzt)")
                print("")
            continue

        if lower == "stats" or lower == "fortschritt":
            habits = list_habits()
            if habits:
                print("\nFortschritt (14 Tage):")
                for h in habits:
                    s = get_habit_stats(h["id"])
                    bar = "=" * (s["rate"] // 10) + "-" * (10 - s["rate"] // 10)
                    print("  " + h["name"] + ": [" + bar + "] " + str(s["rate"]) + "% (Streak: " + str(s["streak"]) + "d)")
                print("")
            # Task-Stats
            from tasks import get_tasks_completed_today
            done_today = len(get_tasks_completed_today())
            open_tasks = len(list_tasks(status="open"))
            print("  Tasks heute: " + str(done_today) + " erledigt, " + str(open_tasks) + " offen\n")
            continue

        # Routing: sim.ai Keywords prüfen
        if contains_simai_keyword(user_input):
            if is_bridge_configured():
                print("Das klingt nach einem sim.ai-claw Task.")
                if confirm("An sim.ai weiterleiten?"):
                    log_action("SIMAI_ROUTE", user_input[:200])
                    result = delegate_to_simai(user_input)
                    print("\nsim.ai: " + result + "\n")
                    continue
                # Bei "n": lokal verarbeiten
            else:
                print("(Das waere ein sim.ai-claw Task, aber Bridge nicht konfiguriert.)")

        # Skill-Matching prüfen
        skill = find_matching_skill(user_input)
        skill_context = ""
        if skill:
            skill_context = "\n\nNutze diesen Skill-Prompt als Leitfaden:\n" + get_skill_prompt(skill["id"])
            increment_usage(skill["id"])
            data_class = CLASS_SKILL
            log_action("SKILL_MATCH", skill["name"])
        else:
            data_class = classify_input(user_input)

        # Nachricht an LLM (Hybrid-Routing nach Datenklasse)
        history.append({"role": "user", "content": user_input})
        if len(history) > 10:
            history = history[-10:]

        log_action("USER", user_input)
        print("... (denke nach)")

        system = _load_system_prompt() + skill_context
        response = chat(history, system, data_class)
        print("\n" + response + "\n")

        history.append({"role": "assistant", "content": response})
        log_action("AGENT", response[:300])

        # Konversation in Memory speichern
        save_memory("conversation", user_input, source="user", session_id=SESSION_ID, importance=3)
        save_memory("conversation", response[:500], source="agent", session_id=SESSION_ID, importance=3)

        # Auto-Entity-Extraktion (im Hintergrund)
        try:
            names = auto_extract_entities(user_input)
            for n in names[:3]:
                create_entity(n, "person")
        except Exception:
            pass

        # Prüfe ob ein Termin vorgeschlagen wurde
        event = parse_calendar_event(response)
        if event:
            print("Termin: " + event["title"])
            print("  Datum: " + event["start"].strftime("%d.%m.%Y %H:%M"))
            print("  Dauer: " + str(event["duration"]) + " Min.")

            if not confirm("Erstellen?"):
                print("Ok, abgebrochen.\n")
                log_action("DENIED", "Termin: " + event["title"])
                continue

            ok, msg = create_event(event["title"], event["start"], event["duration"])
            print(msg + "\n")
            history.append({"role": "user", "content": msg})
            continue

        # Prüfe ob ein Befehl vorgeschlagen wurde
        cmd = parse_command(response)
        if cmd:
            print("Vorgeschlagener Befehl: " + cmd)

            if not confirm("Ausfuehren?"):
                print("Ok, abgebrochen.\n")
                log_action("DENIED", cmd)
                continue

            output, rc = execute_command(cmd)
            status = "OK" if rc == 0 else "FEHLER (rc=" + str(rc) + ")"
            print(status + ":\n" + output + "\n")

            # Ergebnis zur Historie hinzufügen
            result_msg = "Ergebnis von '" + cmd + "':\n" + output
            history.append({"role": "user", "content": result_msg})


def process_message(user_input, history):
    """Verarbeitet eine Nachricht (fuer Terminal und Signal). Gibt Antwort zurück."""
    # Routing: sim.ai Keywords prüfen
    if contains_simai_keyword(user_input):
        if is_bridge_configured():
            log_action("SIMAI_ROUTE", user_input[:200])
            result = delegate_to_simai(user_input)
            return "sim.ai: " + str(result)
        else:
            pass  # Lokal weitermachen

    # Nachricht an LLM
    history.append({"role": "user", "content": user_input})
    if len(history) > 10:
        del history[:-10]

    data_class = classify_input(user_input)
    log_action("USER", user_input)
    response = chat(history, _load_system_prompt(), data_class)
    history.append({"role": "assistant", "content": response})
    log_action("AGENT", response[:300])

    # Termin-Erkennung
    event = parse_calendar_event(response)
    if event:
        return ("TERMIN_VORSCHLAG", event, response)

    # Befehl-Erkennung
    cmd = parse_command(response)
    if cmd:
        return ("BEFEHL_VORSCHLAG", cmd, response)

    return response


def send_morning_heartbeat():
    """Schickt den Morgen-Heartbeat (Tagesplan) via Signal."""
    plan = generate_day_plan()

    # Nudge anfügen
    nudge = get_nudge()
    if nudge:
        plan += "\n\n" + nudge

    plan += "\n\n'plan' / 'tasks' / 'habits' / 'kalender' oder schick eine Aufgabe."
    send_message(plan)
    log_action("HEARTBEAT_SIGNAL", "Tagesplan gesendet")


def signal_loop():
    """Signal-Modus: pollt Nachrichten, verarbeitet, antwortet."""
    setup()
    log_action("START", "KITT v1.0 Signal-Modus gestartet")
    print("KITT v1.0 — Signal-Modus")
    print("Warte auf Nachrichten... (Ctrl+C zum Beenden)\n")

    # Morgen-Heartbeat senden
    send_morning_heartbeat()

    history = []

    while True:
        try:
            messages = receive_messages()
            for msg in messages:
                print("[Signal] " + msg)

                # Sonderbefehle
                if msg.lower() in ("stop", "exit", "quit"):
                    send_message("Agent gestoppt.")
                    log_action("EXIT", "Signal-Stop")
                    return

                if msg.lower() == "kalender":
                    from heartbeat import fetch_calendar_local, parse_icalbuddy_output
                    raw = fetch_calendar_local()
                    events = parse_icalbuddy_output(raw)
                    if events:
                        lines = ["Termine heute:"]
                        for e in events:
                            lines.append(e["time"] + " " + e["subject"])
                        send_message("\n".join(lines))
                    else:
                        send_message("Keine Termine heute.")
                    continue

                # Verarbeiten
                result = process_message(msg, history)

                if isinstance(result, tuple):
                    kind = result[0]
                    if kind == "TERMIN_VORSCHLAG":
                        event = result[1]
                        info = ("Termin: " + event["title"] +
                                "\n" + event["start"].strftime("%d.%m.%Y %H:%M") +
                                " (" + str(event["duration"]) + " Min.)" +
                                "\nErstellen? Antworte 'ja'")
                        send_message(info)
                        # Warte auf Bestätigung
                        confirmed = wait_for_confirmation()
                        if confirmed:
                            ok, reply = create_event(event["title"], event["start"], event["duration"])
                            send_message(reply)
                        else:
                            send_message("Abgebrochen.")
                    elif kind == "BEFEHL_VORSCHLAG":
                        cmd = result[1]
                        send_message("Befehl: " + cmd + "\nAusfuehren? Antworte 'ja'")
                        confirmed = wait_for_confirmation()
                        if confirmed:
                            output, rc = execute_command(cmd)
                            reply = ("OK:\n" if rc == 0 else "FEHLER:\n") + output[:500]
                            send_message(reply)
                        else:
                            send_message("Abgebrochen.")
                            log_action("DENIED", cmd)
                else:
                    send_message(result[:1500])

            time.sleep(5)

        except KeyboardInterrupt:
            print("\nSignal-Modus beendet.")
            log_action("EXIT", "Signal Ctrl+C")
            break


def wait_for_confirmation():
    """Wartet max 60s auf 'ja' via Signal."""
    for _ in range(12):  # 12 x 5s = 60s
        time.sleep(5)
        msgs = receive_messages()
        for m in msgs:
            if m.lower() in ("ja", "j", "yes", "y", "ok"):
                return True
            if m.lower() in ("nein", "n", "no", "abbruch", "stop"):
                return False
    return False


if __name__ == "__main__":
    if "--signal" in sys.argv:
        signal_loop()
    else:
        main()
