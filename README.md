# KITT — Kauz Intelligent Task Tracker

Ein persoenlicher KI-Assistent der lokal auf deinem Rechner laeuft.
Organisiert Arbeit, trackt Gewohnheiten, plant deinen Tag — und den du in einer Stunde lesen kannst.

~2.400 Zeilen Python. 1 Dependency. 0 CVEs.

## Warum nicht OpenClaw / Hermes / n8n-claw?

| Feature | OpenClaw | Hermes | KITT |
|---------|----------|--------|------|
| Codebase | 500.000+ | 50.000+ | ~2.400 |
| Auditierbar | Nein | Schwer | Ja, in 1h |
| CVEs | 60+ | ? | 0 |
| Lokal-first | Nein | Optional | Ja |
| Life Management | Nein | Nein | Ja |
| Habit Tracking | Nein | Nein | Ja |
| Coaching | Nein | Nein | Ja |
| Dependencies | Hunderte | Dutzende | 1 |

## Quick Start

```bash
git clone https://github.com/nicobaar/kitt.git
cd kitt
pip install -r requirements.txt
ollama pull llama3.2:3b
python3 kitt.py
```

KITT startet das Onboarding automatisch. Keine Config-Files, keine ENV-Vars, keine DB-Setup.

## Features

- **Tagesplanung** — Kalender + Tasks + Habits zu einem Tagesplan
- **Projekteverwaltung** — Projekte, Next Actions, Notizen
- **Task-Management** — Prioritaeten, Faelligkeit, Kategorien
- **Habit-Tracking** — Gewohnheiten, Streaks, Fortschrittsbalken
- **Coaching** — Pattern-Erkennung, Nudges, Beobachtungen
- **60 Skills** — Promptbibliothek fuer Analyse, Strategie, Marketing, Coaching
- **Signal-Channel** — E2EE Messaging, Morgen-Heartbeat
- **sim.ai-Bridge** — A2A zu Cloud-Workflows (Email, CRM, LinkedIn)
- **Knowledge Graph** — Personen, Firmen, Projekte verknuepft
- **Onboarding** — 4-Session Kennenlern-Flow
- **Hybrid-LLM** — Lokal (Ollama) fuer Privates, API fuer Arbeit
- **Audit Trail** — Jede Aktion in SQLite geloggt

## Architektur

```
Signal / Terminal
       |
   KITT Core (lokal)
   |-- Ollama (llama3.2:3b, privat)
   |-- Claude API (Arbeit, Skills)
   |-- kitt.db (SQLite)
   |   |-- soul, memory, projects
   |   |-- tasks, habits, skills
   |   |-- kg_entities, sessions, logs
   |-- Module:
   |   |-- planner, review, coach
   |   |-- onboarding, knowledge, skills
   |   |-- calendar, sandbox, bridge
   |
   +-- sim.ai-claw (Cloud, optional)
       |-- Email Agent
       |-- Research Agent
       |-- CRM Agent
```

## Befehle

| Befehl | Was |
|--------|-----|
| `projekte` | Alle Projekte |
| `tasks` | Offene Tasks |
| `neuer task: X` | Task erstellen |
| `erledigt X` | Task abschliessen |
| `plan` | Tagesplan |
| `review` | Tagesrueckblick |
| `habits` | Habits mit Stats |
| `training gemacht` | Habit loggen |
| `stats` | Fortschritt |
| `skills` | Verfuegbare Skills |
| `merk dir: X` | Fakt speichern |
| `was weisst du ueber X` | Memory durchsuchen |

## Datenklassifizierung (ISO 42001)

| Datenklasse | Verarbeitung | Begruendung |
|-------------|-------------|-------------|
| Persoenlich (Habits, Schlaf) | Ollama lokal | Gesundheitsdaten nie in der Cloud |
| Arbeit (Tasks, Projekte) | Claude API | Keine Kundendaten |
| Kundendaten (Email, CRM) | sim.ai Bridge | Guardrails, PII-Filter |

## Signal-Modus

```bash
python3 kitt.py --signal
```

Laeuft als Daemon, pollt Signal-Nachrichten, antwortet automatisch.
Morgen-Heartbeat mit Tagesplan. E2EE by default.

## Ohne sim.ai (Pure Local)

KITT funktioniert komplett ohne Cloud. Dann fehlen Email/CRM/LinkedIn — aber Kalender, Tasks, Projekte, Habits, Coaching funktionieren.

## Lizenz

MIT

## Credits

- Architektur inspiriert von [n8n-claw](https://github.com/freddy-schuetz/n8n-claw) von Friedemann Schuetz
- Gebaut mit [Claude Code](https://claude.ai/claude-code) von Anthropic
- Entwickelt von [kauz.ai](https://kauz.ai)
