# KITT — Kauz Intelligent Task Tracker

Dein persoenlicher KI-Assistent. Lokal, auditierbar, governance-konform.

~1.200 Zeilen Python. 1 Dependency. 0 CVEs.

## Was ist KITT?

Ein KI-Assistent der lokal auf deinem Rechner laeuft, deine Projekte kennt,
deinen Tag strukturiert, deine Gewohnheiten trackt und dich coacht.

Nicht nur ein Arbeitsassistent — ein persoenliches Betriebssystem fuer
Produktivitaet, Gesundheit und Planung.

## Quick Start

```bash
git clone https://github.com/NicolasJanPiero/kitt.git
cd kitt
pip install -r requirements.txt
ollama pull llama3.2:3b
python3 kitt.py
```

KITT fuehrt dich durch ein kurzes Onboarding. Danach ist er einsatzbereit.

## Features

- Lokal first: Ollama + SQLite, kein Cloud-Zwang
- Hybrid-LLM: Sensible Daten lokal, Qualitaet ueber API, Kundendaten ueber Bridge
- Signal: E2EE-Steuerung vom Handy
- Projektmanagement: Projekte, Tasks, Next Actions
- Habit Tracking: Gewohnheiten tracken und Streaks sehen
- Tagesplanung: Kalender + Tasks + Habits = strukturierter Tag
- Coaching: Pattern-Erkennung, Motivations-Nudges
- Reviews: Tages- und Wochenrueckblick mit Statistiken
- Skills: 60 professionelle Prompts als aktives Wissen
- Bridge: Optional an Cloud-Workflows anbindbar (sim.ai, n8n, etc.)
- Reactive Mode: Bestaetigung vor jeder Aktion
- Audit Trail: Jede Aktion geloggt mit Datenklasse
- ISO 42001 / DSGVO ready

## Warum nicht OpenClaw?

| | OpenClaw | KITT |
|---|---|---|
| Codebase | 500.000+ Zeilen | ~1.200 Zeilen |
| CVEs | 60+ bekannt | 0 (lies den Code selbst) |
| Dependencies | Hunderte | 1 (requests) |
| Datenbank | Supabase Cloud | SQLite lokal |
| Modell | Cloud-API only | Hybrid (lokal/API/Bridge) |
| Life Management | Nein | Ja |
| Coaching | Nein | Ja |
| Audit Trail | Nein | Ja, mit Datenklasse |

## Architektur

```
Du (Signal / Terminal)
    |
    v
KITT (lokal)
|-- Ollama (persoenliche Daten, lokal)
|-- Claude API (Arbeit/Coaching, optional)
|-- SQLite (Memory, Projekte, Tasks, Habits)
+-- Bridge -> sim.ai / n8n (Kundendaten, optional)
```

## Befehle

| Befehl | Was |
|--------|-----|
| `kalender` | Heutige Termine |
| `plan` | Tagesplan vorschlagen |
| `wochenplan` | Wochenplan vorschlagen |
| `projekte` | Alle Projekte |
| `projekt <name>` | Projekt-Details |
| `neues projekt: <name>` | Projekt erstellen |
| `tasks` | Offene Aufgaben |
| `neuer task: <titel>` | Task erstellen |
| `erledigt <titel>` | Task abschliessen |
| `habits` | Gewohnheiten mit Stats |
| `training gemacht` | Habit loggen |
| `stats` | Fortschritt |
| `review` | Tagesrueckblick |
| `wochenrueckblick` | Wochenrueckblick |
| `merk dir: <fakt>` | Fakt speichern |
| `was weisst du ueber X` | Memory durchsuchen |
| `skills` | Verfuegbare Skills |
| `heartbeat` | Heartbeat-Vorschlaege |
| `bridge status` | sim.ai Verbindung pruefen |
| `log` | Letzte 20 Aktionen |
| `help` | Alle Befehle |

## Datenklassifizierung (ISO 42001)

| Datenklasse | Verarbeitung | Begruendung |
|-------------|-------------|-------------|
| Persoenlich (Habits, Schlaf) | Ollama lokal | Gesundheitsdaten nie in der Cloud |
| Arbeit (Tasks, Projekte) | Claude API | Keine PII, beste Qualitaet |
| Kundendaten (Email, CRM) | sim.ai Bridge | Guardrails, PII-Filter, Audit |

## Signal-Modus

```bash
export KITT_SIGNAL_NUMBER="+49..."
python3 kitt.py --signal
```

Laeuft als Daemon, pollt Signal-Nachrichten, antwortet automatisch.
Morgen-Heartbeat mit Tagesplan. E2EE by default.

## Konfiguration

Optionale Environment-Variablen:

```
ANTHROPIC_API_KEY     — fuer Claude API (bessere Qualitaet)
SIMAI_WEBHOOK_URL     — fuer sim.ai Bridge
SIMAI_API_KEY         — fuer Bridge-Authentifizierung
KITT_SIGNAL_NUMBER    — fuer Signal-Modus
```

Ohne diese laeuft KITT komplett lokal mit Ollama.

## Modulstruktur

```
kitt.py              — Entry Point
config.py            — Konstanten, Pfade, Keywords
database.py          — SQLite Connection, Schema-Init
llm.py               — Hybrid-LLM-Routing (lokal/API)
agent.py             — Hauptloop, Session-Management
commands.py          — Alle Befehls-Handler
helpers.py           — Parsing, Prompts, Klassifizierung
terminal.py          — Heartbeat-UI
signal_loop.py       — Signal-Modus
memory.py            — Langzeitgedaechtnis
knowledge.py         — Knowledge Graph
projects.py          — Projekt-CRUD
tasks.py             — Task-Management
habits.py            — Habit-Tracking
planner.py           — Tages-/Wochenplanung
review.py            — Tages-/Wochenrueckblick
coach.py             — Nudges, Pattern-Erkennung
skills.py            — Skill-Registry (60 Prompts)
onboarding.py        — 4-Session Kennenlern-Flow
calendar_tool.py     — macOS Kalender (icalBuddy)
sandbox.py           — Shell-Execution, Blocklist
simai_bridge.py      — A2A Bridge zu sim.ai
heartbeat.py         — Reactive Heartbeat
signal_channel.py    — Signal E2EE Channel
schema.sql           — DB-Schema (12 Tabellen)
seed.sql             — Defaults + 60 Skills
```

## Lizenz

MIT

## Credits

- Gebaut mit [Claude Code](https://claude.ai/claude-code) von Anthropic
- Entwickelt von [kauz.ai](https://kauz.ai)
