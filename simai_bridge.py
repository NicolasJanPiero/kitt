"""sim.ai-claw Bridge — A2A-Kommunikation mit Timestamp + Logging."""

import requests
import json
from datetime import datetime
from config import SIMAI_WEBHOOK_URL, SIMAI_API_KEY


def is_bridge_configured():
    """Prüft ob die sim.ai Bridge konfiguriert ist."""
    return bool(SIMAI_WEBHOOK_URL)


def check_bridge_status():
    """Prüft ob sim.ai erreichbar ist."""
    if not is_bridge_configured():
        return "Bridge nicht konfiguriert (SIMAI_WEBHOOK_URL nicht gesetzt)"
    try:
        response = requests.head(SIMAI_WEBHOOK_URL, timeout=5)
        return "sim.ai erreichbar (Status " + str(response.status_code) + ")"
    except requests.ConnectionError:
        return "sim.ai NICHT erreichbar (Connection Error)"
    except requests.Timeout:
        return "sim.ai NICHT erreichbar (Timeout)"


def delegate_to_simai(task, context=""):
    """Sendet einen Task an sim.ai-claw und gibt die Antwort zurück."""
    if not is_bridge_configured():
        return "FEHLER: sim.ai Bridge nicht konfiguriert. Setze SIMAI_WEBHOOK_URL."

    payload = {
        "task": task,
        "context": context,
        "source": "kauz-desktop-agent",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0"
    }

    _log_bridge("SEND", task[:200])

    headers = {"Content-Type": "application/json"}
    if SIMAI_API_KEY:
        headers["X-API-Key"] = SIMAI_API_KEY

    try:
        response = requests.post(
            SIMAI_WEBHOOK_URL, json=payload, headers=headers, timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        output = data.get("output", {})
        if isinstance(output, dict) and "result" in output:
            result = output["result"].get("response", json.dumps(output["result"]))
        else:
            result = data.get("response", data.get("content", json.dumps(data)))
        _log_bridge("RECV", str(result)[:200])
        return result
    except requests.ConnectionError:
        _log_bridge("ERROR", "Connection Error")
        return "FEHLER: sim.ai nicht erreichbar."
    except requests.Timeout:
        _log_bridge("ERROR", "Timeout")
        return "FEHLER: sim.ai Timeout (>30s)."
    except (json.JSONDecodeError, KeyError) as e:
        _log_bridge("ERROR", str(e))
        return "FEHLER: Unerwartete sim.ai Antwort: " + str(e)


def _log_bridge(action, details):
    """Loggt Bridge-Calls in die DB."""
    try:
        from database import log_to_db
        log_to_db("bridge_" + action.lower(), details, module="bridge", data_class="customer")
    except Exception:
        pass
