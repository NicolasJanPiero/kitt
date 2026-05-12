# CLAUDE.md — KITT Development Guide

## Was ist KITT?

Persoenlicher KI-Assistent. Lokal-first, SQLite, Hybrid-LLM, ~2.400 Zeilen Python.

## Repo-Struktur

```
kitt.py              — Entry Point
config.py            — Konstanten, API Keys, Pfade
database.py          — SQLite Connection, Schema-Init
llm.py               — Hybrid-LLM-Routing (lokal/API/Bridge)
agent.py             — Hauptloop, Befehle, Signal-Loop
memory.py            — Langzeitgedaechtnis
knowledge.py         — Knowledge Graph
projects.py          — Projekt-CRUD
tasks.py             — Task-CRUD
habits.py            — Habit-Tracking
planner.py           — Tages-/Wochenplanung
review.py            — Tages-/Wochenrueckblick
coach.py             — Nudges, Pattern-Erkennung
skills.py            — Skill-Registry (60 Prompts)
onboarding.py        — 4-Session Kennenlern-Flow
calendar_tool.py     — macOS Kalender (icalBuddy + AppleScript)
sandbox.py           — Shell-Execution, Pfad-Validierung
signal_channel.py    — Signal E2EE Channel
simai_bridge.py      — A2A Bridge zu sim.ai
heartbeat.py         — Reactive Heartbeat
schema.sql           — DB-Schema (12 Tabellen)
seed.sql             — Initiale Daten + 60 Skills
```

## DB-Schema

12 Tabellen: soul, memory, projects, tasks, habits, habit_log, skills, kg_entities, kg_relations, sessions, heartbeat_rules, logs.

## Coding-Regeln

- Jede Datei < 200 Zeilen (Ausnahme: agent.py als Hauptloop)
- Keine Dependencies ausser requests
- Deutsche Kommentare
- Alle DB-Ops mit try/except
- Logging in logs-Tabelle + Textfile
- Datenklassifizierung: personal→lokal, work→API, customer→Bridge

## Bekannte Limitierungen

- Ollama auf CPU ist langsam (~24s pro Antwort)
- signal-cli startet JVM bei jedem Poll
- Kein Outlook-Calendar-Tool in sim.ai (lokal via icalBuddy)
- Skills werden per Keyword gematcht (kein semantisches Matching)

## Naechste Features

- Desktop-App (Electron oder Swift)
- A2A-Protokoll statt HTTP-Bridge
- Multi-User Support
- Docker-Container fuer VPS-Deployment
- Semantisches Skill-Matching
