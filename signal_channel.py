"""Signal-Channel — Nachrichten senden und empfangen via signal-cli."""

import subprocess
import json
import os
from sandbox import log_action

SIGNAL_NUMBER = os.environ.get("KITT_SIGNAL_NUMBER", "")
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
            [SIGNAL_CLI, "-a", SIGNAL_NUMBER, "--output=json",
             "receive", "--timeout", "1"],
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
            text = None

            # Direkte Nachricht
            dm = envelope.get("dataMessage")
            if dm and dm.get("message"):
                text = dm["message"]

            # Sync-Message (wenn man sich selbst schreibt)
            sync = envelope.get("syncMessage", {}).get("sentMessage")
            if not text and sync and sync.get("message"):
                text = sync["message"]

            if text:
                messages.append(text)
        except json.JSONDecodeError:
            continue

    if messages:
        log_action("SIGNAL_RECV", str(len(messages)) + " msg: " + messages[0][:50])
    return messages
