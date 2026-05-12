"""Knowledge Graph — Entities, Relations, Auto-Extraktion."""

import re
from database import get_db


def create_entity(name, etype, description=None, metadata=None):
    """Erstellt eine Entity (oder ignoriert Duplikate)."""
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO kg_entities (name, type, description, metadata) VALUES (?, ?, ?, ?)",
        (name, etype, description, metadata)
    )
    conn.commit()
    conn.close()


def create_relation(from_name, to_name, relation_type, weight=1.0):
    """Erstellt eine Relation zwischen zwei Entities."""
    conn = get_db()
    f = conn.execute("SELECT id FROM kg_entities WHERE name = ?", (from_name,)).fetchone()
    t = conn.execute("SELECT id FROM kg_entities WHERE name = ?", (to_name,)).fetchone()
    if f and t:
        conn.execute(
            "INSERT INTO kg_relations (from_entity_id, to_entity_id, relation_type, weight) VALUES (?, ?, ?, ?)",
            (f["id"], t["id"], relation_type, weight)
        )
        conn.commit()
    conn.close()


def get_entity(name):
    """Gibt eine Entity zurück."""
    conn = get_db()
    row = conn.execute("SELECT * FROM kg_entities WHERE name LIKE ?", ("%" + name + "%",)).fetchone()
    conn.close()
    return row


def get_entity_relations(entity_name):
    """Gibt alle Relationen einer Entity zurück."""
    conn = get_db()
    entity = conn.execute("SELECT id FROM kg_entities WHERE name LIKE ?", ("%" + entity_name + "%",)).fetchone()
    if not entity:
        conn.close()
        return []
    eid = entity["id"]
    rows = conn.execute(
        "SELECT e2.name, r.relation_type, r.weight FROM kg_relations r "
        "JOIN kg_entities e2 ON (r.to_entity_id = e2.id AND r.from_entity_id = ?) "
        "OR (r.from_entity_id = e2.id AND r.to_entity_id = ?)",
        (eid, eid)
    ).fetchall()
    conn.close()
    return rows


def search_entities(query, etype=None):
    """Sucht Entities nach Name."""
    conn = get_db()
    sql = "SELECT * FROM kg_entities WHERE name LIKE ?"
    params = ["%" + query + "%"]
    if etype:
        sql += " AND type = ?"
        params.append(etype)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def auto_extract_entities(text):
    """Einfache Regex-basierte Entity-Extraktion aus Text."""
    entities = []
    # Grossgeschriebene Woerter (potenzielle Namen/Firmen)
    words = re.findall(r'\b([A-ZÄÖÜ][a-zäöüß]{2,})\b', text)
    # Haeufige Woerter ausfiltern
    stop = {"Der", "Die", "Das", "Ein", "Eine", "Und", "Oder", "Aber", "Wenn",
            "Wie", "Was", "Wer", "Ich", "Mit", "Von", "Bis", "Fuer", "Bei",
            "Nicht", "Noch", "Auch", "Nur", "Mein", "Dein", "Kein", "Alle"}
    return [w for w in set(words) if w not in stop]
