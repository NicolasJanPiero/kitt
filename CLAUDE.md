# CLAUDE.md — KITT Development Guide

## Was ist KITT?

Persoenlicher KI-Assistent. Lokal-first, SQLite, Hybrid-LLM, ~1.200 Zeilen Python.

## Repo-Struktur

```
kitt.py              — Entry Point
config.py            — Konstanten, API Keys, Pfade, Keywords
database.py          — SQLite Connection, Schema-Init
llm.py               — Hybrid-LLM-Routing (lokal/API/Bridge)
agent.py             — Hauptloop, Session-Mgmt, LLM-Routing (~160 Zeilen)
commands.py          — Alle Terminal-Befehle (~180 Zeilen)
helpers.py           — Parsing, Prompts, Klassifizierung (~130 Zeilen)
terminal.py          — Heartbeat-UI (~60 Zeilen)
signal_loop.py       — Signal-Modus (~140 Zeilen)
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
seed.sql             — Allgemeine Defaults + 60 Skills (KEINE persoenlichen Daten)
```

## DB-Schema

12 Tabellen: soul, memory, projects, tasks, habits, habit_log, skills, kg_entities, kg_relations, sessions, heartbeat_rules, logs.

## Coding-Regeln

- Jede Datei < 200 Zeilen
- Keine Dependencies ausser requests
- Deutsche Kommentare
- Alle DB-Ops mit try/except
- Logging in logs-Tabelle + Textfile
- Datenklassifizierung: personal->lokal, work->API, customer->Bridge
- seed.sql: NUR allgemeine Defaults, keine persoenlichen Daten

## Multi-User

- Beim ersten Start: DB wird aus schema.sql + seed.sql erstellt
- Onboarding startet automatisch (onboarding_complete='false')
- User gibt Name, Job, Projekte, Habits ein
- Alles in lokaler kitt.db gespeichert
- Kein hardcodierter Username im Code

## Bekannte Limitierungen

- Ollama auf CPU ist langsam (~24s pro Antwort)
- signal-cli startet JVM bei jedem Poll
- Skills werden per Keyword gematcht (kein semantisches Matching)
