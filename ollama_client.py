import json
import requests
from config import OLLAMA_MODEL, SOUL_PATH

# Native Ollama API (stabiler als OpenAI-Kompatibilitätsschicht)
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"


def load_soul():
    """Lädt SOUL.md als System-Prompt."""
    try:
        with open(SOUL_PATH, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "Du bist ein hilfreicher Assistent. Antworte kurz und auf Deutsch."


def chat(messages):
    """Sendet Nachrichten an Ollama und gibt die Antwort zurück."""
    system_prompt = load_soul()
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    try:
        response = requests.post(
            OLLAMA_CHAT_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": full_messages,
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]
    except requests.ConnectionError:
        return "FEHLER: Ollama läuft nicht. Starte mit: ollama serve"
    except requests.Timeout:
        return "FEHLER: Ollama-Timeout (>120s). Modell überlastet."
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        return "FEHLER: Unerwartete Ollama-Antwort: " + str(e)
