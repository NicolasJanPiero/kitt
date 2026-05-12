"""Hybrid-LLM-Routing nach Datenklasse (ISO 42001 / DSGVO Art. 32)."""

import json
import time
import requests
from config import OLLAMA_MODEL, ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from database import log_to_db

# Datenklassen
CLASS_PERSONAL = "personal"   # Gesundheit, Habits, Schlaf → nur lokal
CLASS_WORK = "work"           # Tasks, Projekte, Planung → API erlaubt
CLASS_CUSTOMER = "customer"   # Kundendaten, CRM, Email → nur sim.ai Bridge
CLASS_SKILL = "skill"         # Promptbibliothek ausführen → API (Qualität)

OLLAMA_URL = "http://localhost:11434/api/chat"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


def chat(messages, system_prompt=None, data_class=CLASS_WORK):
    """Routet an das richtige LLM basierend auf Datenklasse."""
    start = time.time()

    if data_class == CLASS_PERSONAL:
        result = _call_ollama(messages, system_prompt)
        provider = "ollama"
    elif data_class == CLASS_CUSTOMER:
        result = "Kundendaten werden nicht lokal verarbeitet. Nutze die sim.ai Bridge."
        provider = "blocked"
    elif ANTHROPIC_API_KEY:
        result = _call_anthropic(messages, system_prompt)
        provider = "anthropic"
    else:
        result = _call_ollama(messages, system_prompt)
        provider = "ollama_fallback"

    duration = int((time.time() - start) * 1000)
    log_to_db("llm_call", provider + "|" + data_class,
              result[:200] if result else None,
              module="llm", data_class=data_class, duration_ms=duration)
    return result


def _call_ollama(messages, system_prompt=None):
    """Lokaler Ollama-Call (privat, kein Datenabfluss)."""
    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "messages": full_messages,
            "stream": False,
        }, timeout=120)
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    except requests.ConnectionError:
        return "FEHLER: Ollama laeuft nicht. Starte mit: ollama serve"
    except requests.Timeout:
        return "FEHLER: Ollama-Timeout (>120s)."
    except (KeyError, json.JSONDecodeError) as e:
        return "FEHLER: Ollama-Antwort: " + str(e)


def _call_anthropic(messages, system_prompt=None):
    """Claude API Call (fuer Arbeits-Tasks, Skills, Coaching)."""
    api_messages = []
    for m in messages:
        if m["role"] in ("user", "assistant"):
            api_messages.append({"role": m["role"], "content": m["content"]})

    body = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 2048,
        "messages": api_messages,
    }
    if system_prompt:
        body["system"] = system_prompt

    try:
        resp = requests.post(ANTHROPIC_URL, json=body, headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }, timeout=30)
        if resp.status_code != 200:
            return _call_ollama(messages, system_prompt)  # Fallback
        data = resp.json()
        return data["content"][0]["text"]
    except (requests.ConnectionError, requests.Timeout):
        return _call_ollama(messages, system_prompt)  # Fallback
    except (KeyError, json.JSONDecodeError):
        return _call_ollama(messages, system_prompt)  # Fallback
