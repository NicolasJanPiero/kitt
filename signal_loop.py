"""Signal-Modus — Nachrichten-Polling, Verarbeitung, Antwort via Signal."""

import time
from datetime import date, datetime
from helpers import (classify_input, contains_simai_keyword, load_system_prompt,
                     parse_calendar_event, parse_command)
from llm import chat
from sandbox import execute_command, log_action
from simai_bridge import delegate_to_simai, is_bridge_configured
from signal_channel import send_message, receive_messages
from planner import generate_day_plan
from coach import get_nudge
from calendar_tool import create_event
from heartbeat import fetch_calendar_local, parse_icalbuddy_output


def process_message(user_input, history):
    """Verarbeitet eine Nachricht. Gibt Antwort zurueck."""
    if contains_simai_keyword(user_input) and is_bridge_configured():
        log_action("SIMAI_ROUTE", user_input[:200])
        result = delegate_to_simai(user_input)
        return "sim.ai: " + str(result)

    history.append({"role": "user", "content": user_input})
    if len(history) > 10:
        del history[:-10]

    data_class = classify_input(user_input)
    log_action("USER", user_input)
    response = chat(history, load_system_prompt(), data_class)
    history.append({"role": "assistant", "content": response})
    log_action("AGENT", response[:300])

    event = parse_calendar_event(response)
    if event:
        return ("TERMIN_VORSCHLAG", event, response)
    cmd = parse_command(response)
    if cmd:
        return ("BEFEHL_VORSCHLAG", cmd, response)
    return response


def send_morning_heartbeat():
    """Schickt den Morgen-Heartbeat (Tagesplan) via Signal."""
    plan = generate_day_plan()
    nudge = get_nudge()
    if nudge:
        plan += "\n\n" + nudge
    plan += "\n\n'plan' / 'tasks' / 'habits' / 'kalender' oder schick eine Aufgabe."
    send_message(plan)
    log_action("HEARTBEAT_SIGNAL", "Tagesplan gesendet")


def wait_for_confirmation():
    """Wartet max 60s auf 'ja' via Signal."""
    for _ in range(12):
        time.sleep(5)
        msgs = receive_messages()
        for m in msgs:
            if m.lower() in ("ja", "j", "yes", "y", "ok"):
                return True
            if m.lower() in ("nein", "n", "no", "abbruch", "stop"):
                return False
    return False


def handle_signal_result(result, history):
    """Verarbeitet Signal-Antwort (Termin/Befehl/Text)."""
    if not isinstance(result, tuple):
        send_message(result[:1500])
        return

    kind = result[0]
    if kind == "TERMIN_VORSCHLAG":
        event = result[1]
        info = ("Termin: " + event["title"] + "\n" +
                event["start"].strftime("%d.%m.%Y %H:%M") +
                " (" + str(event["duration"]) + " Min.)" +
                "\nErstellen? Antworte 'ja'")
        send_message(info)
        if wait_for_confirmation():
            ok, reply = create_event(event["title"], event["start"], event["duration"])
            send_message(reply)
        else:
            send_message("Abgebrochen.")
    elif kind == "BEFEHL_VORSCHLAG":
        cmd = result[1]
        send_message("Befehl: " + cmd + "\nAusfuehren? Antworte 'ja'")
        if wait_for_confirmation():
            output, rc = execute_command(cmd)
            reply = ("OK:\n" if rc == 0 else "FEHLER:\n") + output[:500]
            send_message(reply)
        else:
            send_message("Abgebrochen.")
            log_action("DENIED", cmd)


def signal_loop(setup_fn):
    """Signal-Modus: pollt Nachrichten, verarbeitet, antwortet."""
    setup_fn("signal")
    log_action("START", "KITT v1.0 Signal-Modus gestartet")
    print("KITT v1.0 -- Signal-Modus")
    print("Warte auf Nachrichten... (Ctrl+C zum Beenden)\n")

    send_morning_heartbeat()
    last_heartbeat_date = date.today()
    history = []

    while True:
        try:
            today = date.today()
            if today != last_heartbeat_date and datetime.now().hour >= 7:
                send_morning_heartbeat()
                last_heartbeat_date = today

            messages = receive_messages()
            for msg in messages:
                print("[Signal] " + msg)
                if msg.lower() in ("stop", "exit", "quit"):
                    send_message("Agent gestoppt.")
                    log_action("EXIT", "Signal-Stop")
                    return
                if msg.lower() == "kalender":
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

                result = process_message(msg, history)
                handle_signal_result(result, history)

            time.sleep(5)
        except KeyboardInterrupt:
            print("\nSignal-Modus beendet.")
            log_action("EXIT", "Signal Ctrl+C")
            break
