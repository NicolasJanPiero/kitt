#!/usr/bin/env python3
"""KITT v1.0 — Hauptloop, Session-Management, LLM-Routing."""

import os
import uuid
from config import WORKSPACE, LOG_DIR
from database import init_db, get_db
from llm import chat, CLASS_SKILL
from memory import save_memory
from onboarding import is_onboarding_needed, run_onboarding
from knowledge import auto_extract_entities, create_entity
from sandbox import execute_command, log_action
from simai_bridge import delegate_to_simai, is_bridge_configured
from heartbeat import show_heartbeat
from calendar_tool import create_event
from coach import get_nudge
from skills import find_matching_skill, get_skill_prompt, increment_usage
from helpers import (parse_command, parse_calendar_event, confirm,
                     classify_input, contains_simai_keyword, load_system_prompt)
from terminal import handle_heartbeat_choice
from commands import handle_command

SESSION_ID = str(uuid.uuid4())[:8]


def setup(channel="terminal"):
    """Erstellt Workspace, initialisiert DB, registriert Session."""
    os.makedirs(WORKSPACE, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    is_new = init_db()
    if is_new:
        print("Datenbank erstellt: kitt.db")
    try:
        conn = get_db()
        conn.execute("INSERT OR IGNORE INTO sessions (id, channel) VALUES (?, ?)",
                     (SESSION_ID, channel))
        conn.commit()
        conn.close()
    except Exception:
        pass


def handle_llm(user_input, history):
    """Routet an LLM mit sim.ai-Check, Skill-Matching, Termin/Befehl-Parsing."""
    # sim.ai Routing
    if contains_simai_keyword(user_input):
        if is_bridge_configured():
            print("Das klingt nach einem sim.ai-claw Task.")
            if confirm("An sim.ai weiterleiten?"):
                log_action("SIMAI_ROUTE", user_input[:200])
                result = delegate_to_simai(user_input)
                print("\nsim.ai: " + result + "\n")
                return
        else:
            print("(Das waere ein sim.ai-claw Task, aber Bridge nicht konfiguriert.)")

    # Skill-Matching
    skill = find_matching_skill(user_input)
    skill_context = ""
    if skill:
        skill_context = "\n\nNutze diesen Skill-Prompt als Leitfaden:\n" + get_skill_prompt(skill["id"])
        increment_usage(skill["id"])
        data_class = CLASS_SKILL
        log_action("SKILL_MATCH", skill["name"])
    else:
        data_class = classify_input(user_input)

    # LLM-Call
    history.append({"role": "user", "content": user_input})
    if len(history) > 10:
        history[:] = history[-10:]
    log_action("USER", user_input)
    print("... (denke nach)")

    system = load_system_prompt() + skill_context
    response = chat(history, system, data_class)
    print("\n" + response + "\n")

    history.append({"role": "assistant", "content": response})
    log_action("AGENT", response[:300])
    save_memory("conversation", user_input, source="user", session_id=SESSION_ID, importance=3)
    save_memory("conversation", response[:500], source="agent", session_id=SESSION_ID, importance=3)

    # Auto-Entity-Extraktion
    try:
        for n in auto_extract_entities(user_input)[:3]:
            create_entity(n, "person")
    except Exception:
        pass

    # Termin/Befehl-Parsing
    event = parse_calendar_event(response)
    if event:
        print("Termin: " + event["title"])
        print("  Datum: " + event["start"].strftime("%d.%m.%Y %H:%M"))
        print("  Dauer: " + str(event["duration"]) + " Min.")
        if confirm("Erstellen?"):
            ok, msg = create_event(event["title"], event["start"], event["duration"])
            print(msg + "\n")
            history.append({"role": "user", "content": msg})
        else:
            print("Ok, abgebrochen.\n")
            log_action("DENIED", "Termin: " + event["title"])
        return

    cmd = parse_command(response)
    if cmd:
        print("Vorgeschlagener Befehl: " + cmd)
        if confirm("Ausfuehren?"):
            output, rc = execute_command(cmd)
            status = "OK" if rc == 0 else "FEHLER (rc=" + str(rc) + ")"
            print(status + ":\n" + output + "\n")
            history.append({"role": "user", "content": "Ergebnis von '" + cmd + "':\n" + output})
        else:
            print("Ok, abgebrochen.\n")
            log_action("DENIED", cmd)


def main():
    """Terminal-Hauptloop."""
    setup()
    log_action("START", "KITT v1.0 gestartet")

    if is_onboarding_needed():
        run_onboarding()

    print("KITT v1.0 — Reactive Mode (Session " + SESSION_ID + ")")
    if is_bridge_configured():
        print("sim.ai Bridge: aktiv")
    print("Was soll ich tun? (help fuer Befehle)\n")

    suggestions = show_heartbeat()
    if suggestions:
        handle_heartbeat_choice(suggestions)

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

        if not handle_command(user_input, user_input.lower(), SESSION_ID):
            handle_llm(user_input, history)


def signal_loop():
    """Wrapper fuer Signal-Modus."""
    from signal_loop import signal_loop as _signal_loop
    _signal_loop(setup)
