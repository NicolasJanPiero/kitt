"""Onboarding — Kennenlern-Flow für neue User (Session 1+2)."""

from database import get_db
from memory import save_memory


def _ask(question):
    """Stellt eine Frage und gibt die Antwort zurück."""
    try:
        return input(question + "\n> ").strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def _set_soul(key, value):
    """Setzt einen Wert in der soul-Tabelle."""
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO soul (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def _add_entity(name, etype, description=None):
    """Erstellt eine Knowledge-Graph Entity."""
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO kg_entities (name, type, description) VALUES (?, ?, ?)",
        (name, etype, description)
    )
    conn.commit()
    conn.close()


def is_onboarding_needed():
    """Prüft ob Onboarding nötig ist."""
    conn = get_db()
    row = conn.execute("SELECT value FROM soul WHERE key='onboarding_complete'").fetchone()
    conn.close()
    return row and row["value"] == "false"


def run_onboarding():
    """Startet den Onboarding-Flow (Session 1+2)."""
    conn = get_db()
    row = conn.execute("SELECT value FROM soul WHERE key='onboarding_complete'").fetchone()
    status = row["value"] if row else "false"
    conn.close()

    if status == "true":
        return False

    if status == "false":
        print("\nHallo! Ich bin KITT — dein persoenlicher Assistent.")
        print("Bevor ich dir helfen kann, will ich dich kennenlernen.\n")
        _session_1()
        _session_2()
    elif status == "partial_s1":
        _session_2()
    elif status == "partial_s2":
        _session_3()
        _session_4()
    elif status == "partial_s3":
        _session_4()
    return True


def _session_1():
    """Basics: Name, Job, Tools, Produktivität."""
    name = _ask("Wie heisst du?")
    if not name:
        return
    _set_soul("owner_name", name)
    _add_entity(name, "person", "Owner/User von KITT")

    print("\nHi " + name + ". Ein paar kurze Fragen:\n")

    job = _ask("1. Was ist dein Job? (Branche, Rolle, was du den ganzen Tag machst)")
    if job:
        save_memory("fact", "Job: " + job, source="onboarding", tags="job,rolle", importance=8)

    tools = _ask("\n2. Welche Tools nutzt du taeglich?")
    if tools:
        save_memory("preference", "Taegliche Tools: " + tools, source="onboarding", tags="tools", importance=6)

    produktiv = _ask("\n3. Arbeitest du eher morgens produktiv oder abends?")
    if produktiv:
        save_memory("preference", "Produktivste Zeit: " + produktiv, source="onboarding", tags="produktivitaet", importance=7)

    planung = _ask("\n4. Wie planst du deine Woche normalerweise?")
    if planung:
        save_memory("preference", "Wochenplanung: " + planung, source="onboarding", tags="planung", importance=5)

    # Knowledge Graph: Firma extrahieren falls erwaehnt
    if job:
        for word in ["bei ", "at ", "fuer "]:
            if word in job.lower():
                firma = job.lower().split(word, 1)[1].split(",")[0].split(".")[0].strip()
                if firma:
                    _add_entity(firma, "company")
                break

    _set_soul("onboarding_complete", "partial_s1")
    print("\nOK. Ich merke mir das alles.\n")


def _session_2():
    """Projekte: laufende Projekte mit Details."""
    conn = get_db()
    row = conn.execute("SELECT value FROM soul WHERE key='owner_name'").fetchone()
    name = row["value"] if row else "du"
    conn.close()

    print("Jetzt zu deinen Projekten, " + name + ".\n")
    projekte = _ask("Welche Projekte laufen bei dir gerade? (kommasepariert)")
    if not projekte:
        _set_soul("onboarding_complete", "partial_s2")
        return

    projekt_namen = [p.strip() for p in projekte.split(",") if p.strip()]
    print("\n" + str(len(projekt_namen)) + " Projekte. Kurz durch jeden:\n")

    for p_name in projekt_namen:
        beschreibung = _ask(p_name + " — worum geht's?")
        naechster = _ask(p_name + " — was ist der naechste Schritt?")
        conn = get_db()
        conn.execute(
            "INSERT OR REPLACE INTO projects (name, description, next_action, status) VALUES (?, ?, ?, 'active')",
            (p_name, beschreibung, naechster)
        )
        conn.commit()
        conn.close()
        _add_entity(p_name, "project", beschreibung)
        print("")

    _set_soul("onboarding_complete", "partial_s2")
    print("Projekte gespeichert.\n")
    _session_3()
    _session_4()


def _session_3():
    """Gesundheit & Gewohnheiten."""
    from habits import create_habit

    print("Jetzt zu deinen Gewohnheiten und Zielen.\n")

    sport = _ask("1. Machst du regelmaessig Sport? Wenn ja, was und wie oft?")
    if sport:
        save_memory("preference", "Sport: " + sport, source="onboarding", tags="sport,gesundheit", importance=7)
        # Habit erstellen
        freq = "3x_week"
        if "taeglich" in sport.lower() or "jeden tag" in sport.lower():
            freq = "daily"
        elif "2x" in sport or "zweimal" in sport.lower():
            freq = "2x_week"
        create_habit("Training", category="sport", target_frequency=freq, target_description=sport)

    andere = _ask("\n2. Andere Gewohnheiten die du aufbauen willst?")
    if andere:
        save_memory("preference", "Gewohnheitsziele: " + andere, source="onboarding", tags="habits", importance=6)
        for h in andere.split(","):
            h = h.strip()
            if h:
                create_habit(h, category="mental", target_frequency="daily")

    schwaechen = _ask("\n3. Was faellt dir am schwersten durchzuziehen?")
    if schwaechen:
        save_memory("fact", "Challenge: " + schwaechen, source="onboarding", tags="schwaeche", importance=7)

    schlaf = _ask("\n4. Wann gehst du ins Bett, wann stehst du auf?")
    if schlaf:
        save_memory("preference", "Schlaf: " + schlaf, source="onboarding", tags="schlaf,gesundheit", importance=6)

    _set_soul("onboarding_complete", "partial_s3")
    print("\nVerstanden. Ich tracke deine Habits ab jetzt.\n")


def _session_4():
    """Arbeitsweise & Kommunikation."""
    print("Letzte Runde: Wie soll ich mit dir kommunizieren?\n")

    stil = _ask("1. Kurz und direkt, oder ausfuehrlich mit Erklaerungen?")
    duzen = _ask("\n2. Duzen oder siezen?")
    vorschlaege = _ask("\n3. Darf ich Vorschlaege machen die du nicht gefragt hast?")
    deferred = _ask("\n4. Wie soll ich reagieren wenn du einen Task seit 3 Tagen verschiebst?")
    review = _ask("\n5. Soll ich einen Wochenrueckblick machen? Wenn ja, welcher Tag?")

    # Preferences speichern
    prefs = []
    if stil:
        prefs.append("Kommunikationsstil: " + stil)
    if duzen:
        prefs.append("Anrede: " + duzen)
    if vorschlaege:
        prefs.append("Proaktive Vorschlaege: " + vorschlaege)
    if deferred:
        prefs.append("Bei verschobenen Tasks: " + deferred)
    if review:
        prefs.append("Wochenrueckblick: " + review)

    for p in prefs:
        save_memory("preference", p, source="onboarding", tags="kommunikation", importance=8)

    _set_soul("onboarding_complete", "true")
    print("\nOnboarding abgeschlossen. Ich kenne dich jetzt. Sag mir was ansteht.\n")
