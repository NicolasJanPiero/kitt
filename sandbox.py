import os
import subprocess
from datetime import datetime
from config import ALLOWED_DIRS, BLOCKED_COMMANDS, WORKSPACE, LOG_DIR


def is_safe_path(path):
    """Prüft ob ein Pfad innerhalb der erlaubten Verzeichnisse liegt."""
    resolved = os.path.realpath(os.path.expanduser(path))
    return any(resolved.startswith(os.path.realpath(d)) for d in ALLOWED_DIRS)


def is_safe_command(cmd):
    """Prüft ob ein Befehl auf der Blocklist steht."""
    cmd_lower = cmd.lower()
    for blocked in BLOCKED_COMMANDS:
        if blocked.lower() in cmd_lower:
            return False
    return True


def execute_command(cmd):
    """Führt einen Shell-Befehl in der Sandbox aus. Gibt (output, returncode) zurück."""
    if not is_safe_command(cmd):
        msg = "BLOCKIERT: Befehl auf der Sicherheits-Blocklist."
        log_action("BLOCKED", cmd)
        return msg, 1

    log_action("EXECUTE", cmd)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=WORKSPACE,
        )
        output = result.stdout + result.stderr
        if not output.strip():
            output = "(kein Output)"
        log_action("RESULT", "rc=" + str(result.returncode) + " | " + output[:200])
        return output, result.returncode
    except subprocess.TimeoutExpired:
        log_action("TIMEOUT", cmd)
        return "FEHLER: Befehl-Timeout (>30s)", 1


def log_action(action, details):
    """Loggt eine Aktion in Textfile + SQLite."""
    os.makedirs(LOG_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    logfile = os.path.join(LOG_DIR, today + ".log")
    timestamp = datetime.now().isoformat()
    line = timestamp + " | " + action + " | " + details.replace("\n", " ")[:500] + "\n"
    with open(logfile, "a") as f:
        f.write(line)
    try:
        from database import log_to_db
        log_to_db(action, details[:500], module="sandbox")
    except Exception:
        pass
