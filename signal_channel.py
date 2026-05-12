"""Signal-Channel — Nachrichten senden und empfangen via signal-cli."""

import subprocess
import json
import os
from sandbox import log_action

SIGNAL_NUMBER = "+491637760077"
SIGNAL_CLI = "signal-cli"
JAVA_PATH = "/usr/local/opt/openjdk/bin"


def _env():
    """Gibt Environment mit Java im PATH zurück."""
    env = os.environ.copy()
    env["PATH"] = JAVA_PATH + ":" + env.get("PATH", "")
    return env


def send_message(text, recipient=None):
    """Sendet eine Nachricht an Nicos Signal-Nummer."""
    to = recipient or SIGNAL_NUMBER
    try:
        result = subprocess.run(
            [SIGNAL_CLI, "-a", SIGNAL_NUMBER, "send", "-m", text, to],
            capture_output=True, text=True, timeout=15, env=_env()
        )
        if result.returncode == 0:
            log_action("SIGNAL_SEND", text[:100])
            return True
        else:
            log_action("SIGNAL_ERROR", result.stderr[:200])
            return False
    except subprocess.TimeoutExpired:
        log_action("SIGNAL_ERROR", "send timeout")
        return False


def receive_messages():
    """Holt neue Nachrichten. Gibt Liste von Strings zurück."""
    try:
        result = subprocess.run(
            [SIGNAL_CLI, "-a", SIGNAL_NUMBER, "receive",
             "--timeout", "1", "--json"],
            capture_output=True, text=True, timeout=10, env=_env()
        )
    except subprocess.TimeoutExpired:
        return []

    messages = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        try:
            data = json.loads(line)
            envelope = data.get("envelope", {})
            msg = envelope.get("dataMessage", {})
            text = msg.get("message", "")
            sender = envelope.get("source", "")
            # Nur Nachrichten von Nico, keine eigenen Sync-Messages
            if text and sender == SIGNAL_NUMBER:
                messages.append(text)
        except json.JSONDecodeError:
            continue

    if messages:
        log_action("SIGNAL_RECV", str(len(messages)) + " Nachrichten")
    return messages
