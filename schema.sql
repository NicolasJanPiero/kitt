-- KITT Schema v1.0

-- Persönlichkeit und Konfiguration
CREATE TABLE IF NOT EXISTS soul (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Langzeitgedächtnis
CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT DEFAULT 'user',
    tags TEXT,
    entity_name TEXT,
    importance INTEGER DEFAULT 5,
    expires_at TEXT,
    session_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_memory_type ON memory(type);
CREATE INDEX IF NOT EXISTS idx_memory_tags ON memory(tags);
CREATE INDEX IF NOT EXISTS idx_memory_entity ON memory(entity_name);
CREATE INDEX IF NOT EXISTS idx_memory_created ON memory(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory(importance DESC);

-- Projektverwaltung
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'active',
    description TEXT,
    notes TEXT,
    priority INTEGER DEFAULT 5,
    tags TEXT,
    next_action TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Aufgaben
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    project_id INTEGER,
    status TEXT DEFAULT 'open',
    priority TEXT DEFAULT 'medium',
    category TEXT,
    due_date TEXT,
    reminder_at TEXT,
    recurring TEXT,
    energy_level TEXT,
    estimated_minutes INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);

-- Gewohnheiten
CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    target_frequency TEXT,
    target_description TEXT,
    reminder_time TEXT,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS habit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    completed INTEGER DEFAULT 0,
    notes TEXT,
    logged_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (habit_id) REFERENCES habits(id),
    UNIQUE(habit_id, date)
);
CREATE INDEX IF NOT EXISTS idx_habit_log_date ON habit_log(date DESC);
CREATE INDEX IF NOT EXISTS idx_habit_log_habit ON habit_log(habit_id);

-- Skills (Promptbibliothek)
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT,
    trigger_keywords TEXT,
    prompt TEXT NOT NULL,
    target TEXT DEFAULT 'local',
    response_format TEXT,
    enabled INTEGER DEFAULT 1,
    usage_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Knowledge Graph
CREATE TABLE IF NOT EXISTS kg_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    metadata TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(name, type)
);

CREATE TABLE IF NOT EXISTS kg_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_entity_id INTEGER NOT NULL,
    to_entity_id INTEGER NOT NULL,
    relation_type TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    metadata TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (from_entity_id) REFERENCES kg_entities(id),
    FOREIGN KEY (to_entity_id) REFERENCES kg_entities(id)
);
CREATE INDEX IF NOT EXISTS idx_kg_entities_type ON kg_entities(type);
CREATE INDEX IF NOT EXISTS idx_kg_relations_from ON kg_relations(from_entity_id);
CREATE INDEX IF NOT EXISTS idx_kg_relations_to ON kg_relations(to_entity_id);

-- Sessions
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    channel TEXT DEFAULT 'terminal',
    started_at TEXT DEFAULT (datetime('now')),
    ended_at TEXT,
    summary TEXT,
    mood TEXT
);

-- Heartbeat-Regeln
CREATE TABLE IF NOT EXISTS heartbeat_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    schedule TEXT NOT NULL,
    time_of_day TEXT,
    category TEXT,
    action_type TEXT NOT NULL,
    action_data TEXT NOT NULL,
    description TEXT,
    enabled INTEGER DEFAULT 1,
    last_run TEXT
);

-- Audit Trail
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    input TEXT,
    output TEXT,
    confirmed INTEGER,
    channel TEXT DEFAULT 'terminal',
    module TEXT,
    data_class TEXT,
    duration_ms INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_logs_action ON logs(action);
CREATE INDEX IF NOT EXISTS idx_logs_created ON logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_module ON logs(module);
