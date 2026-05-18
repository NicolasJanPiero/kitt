"""Terminal-Modus — Heartbeat-UI und interaktive Elemente."""

from helpers import confirm
from sandbox import execute_command, log_action
from simai_bridge import delegate_to_simai, is_bridge_configured


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
    """Fuehrt einen Heartbeat-Vorschlag aus (mit Bestaetigung)."""
    print("\n  " + item["name"] + ": " + item["description"])

    if item.get("handler") == "calendar":
        if confirm("  Outlook-Kalender abrufen?"):
            from heartbeat import handle_calendar_response
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
