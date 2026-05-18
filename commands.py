"""Befehls-Handler — Alle Terminal-Befehle als Funktionen."""

from config import LOG_DIR
from memory import save_memory, search_memory, get_recent_memories
from projects import list_projects, get_project, create_project, format_projects
from tasks import (list_tasks, create_task, complete_task, find_task,
                   format_tasks, get_tasks_completed_today)
from planner import generate_day_plan, generate_week_plan
from review import generate_day_review, generate_week_review
from habits import list_habits, find_habit, log_habit, get_habit_stats, get_today_habits
from skills import list_skills
from simai_bridge import check_bridge_status
from heartbeat import show_heartbeat, fetch_calendar_local, parse_icalbuddy_output
from sandbox import log_action
from helpers import show_help, show_log
from terminal import handle_heartbeat_choice


def handle_command(user_input, lower, session_id):
    """Verarbeitet einen Befehl. Gibt True zurueck wenn behandelt."""
    # System
    if lower == "log":
        show_log(LOG_DIR)
        return True
    if lower == "help":
        show_help()
        return True
    if lower == "heartbeat":
        s = show_heartbeat()
        if s:
            handle_heartbeat_choice(s)
        else:
            print("(Keine Vorschlaege fuer heute)")
        return True
    if lower == "bridge status":
        print(check_bridge_status())
        return True
    if lower in ("kalender", "termine"):
        raw = fetch_calendar_local()
        events = parse_icalbuddy_output(raw)
        if events:
            print("\nTermine heute:")
            for e in events:
                line = "  " + e["time"] + "  " + e["subject"]
                if e["attendees"]:
                    line += " (" + e["attendees"] + ")"
                print(line)
            print("  " + str(len(events)) + " Termine\n")
        else:
            print("Keine Termine heute.\n")
        return True

    # Memory
    if lower.startswith(("merk dir", "merke dir", "remember")):
        fact = user_input.split(":", 1)[1].strip() if ":" in user_input else user_input.split(" ", 2)[-1]
        save_memory("fact", fact, source="user", importance=7, session_id=session_id)
        print("Gemerkt: " + fact + "\n")
        log_action("MEMORY_SAVE", fact)
        return True
    if lower.startswith(("was weisst du", "was weißt du")):
        query = user_input.split("ueber")[-1].split("über")[-1].strip().rstrip("?")
        if not query or query == user_input or query in ("mich", "mir", "meine"):
            query = ""
        results = search_memory(query) if query else get_recent_memories(limit=10)
        if results:
            print("\nDas weiss ich:")
            for r in results[:10]:
                print("  [" + r["type"] + "] " + r["content"][:100])
            print("")
        else:
            print("Dazu habe ich noch nichts gespeichert.\n")
        return True

    # Projekte
    if lower == "projekte":
        print("\n" + format_projects(list_projects()) + "\n")
        return True
    if lower.startswith("projekt "):
        p = get_project(user_input[8:].strip())
        if p:
            print("\n  " + p["name"] + " (Prio " + str(p["priority"]) + ", " + p["status"] + ")")
            if p["description"]:
                print("  " + p["description"])
            if p["next_action"]:
                print("  Next: " + p["next_action"])
            if p["notes"]:
                print("  Notizen:\n  " + p["notes"].replace("\n", "\n  "))
            print("")
        else:
            print("Projekt nicht gefunden.\n")
        return True
    if lower.startswith("neues projekt"):
        name = user_input.split(":", 1)[1].strip() if ":" in user_input else user_input[14:].strip()
        if name:
            create_project(name)
            print("Projekt erstellt: " + name + "\n")
        else:
            print("Nutzung: neues projekt: Name\n")
        return True

    # Tasks
    if lower in ("tasks", "aufgaben"):
        print("\n" + format_tasks(list_tasks()) + "\n")
        return True
    if lower.startswith(("neuer task", "neue aufgabe")):
        title = user_input.split(":", 1)[1].strip() if ":" in user_input else user_input.split(" ", 2)[-1]
        if title and title not in ("task", "aufgabe"):
            create_task(title)
            print("Task erstellt: " + title + "\n")
        else:
            print("Nutzung: neuer task: Titel\n")
        return True
    if lower.startswith("erledigt"):
        query = user_input[8:].strip().lstrip(":").strip()
        if query:
            t = find_task(query)
            if t:
                complete_task(t["id"])
                print("Erledigt: " + t["title"] + "\n")
            else:
                print("Task nicht gefunden: " + query + "\n")
        else:
            print("Nutzung: erledigt Taskname\n")
        return True

    # Planung + Review
    if lower in ("plan", "tagesplan"):
        print("\n" + generate_day_plan() + "\n")
        return True
    if lower in ("wochenplan", "woche"):
        print("\n" + generate_week_plan() + "\n")
        return True
    if lower in ("review", "rueckblick", "tagesrueckblick"):
        print("\n" + generate_day_review() + "\n")
        return True
    if lower in ("wochenrueckblick", "wochenreview"):
        print("\n" + generate_week_review() + "\n")
        return True

    # Habits
    if lower in ("habits", "gewohnheiten"):
        habits = get_today_habits()
        if habits:
            print("\nHabits heute:")
            for h in habits:
                status = "[x]" if h["done_today"] else "[ ]"
                stats = get_habit_stats(h["id"])
                print("  " + status + " " + h["name"] +
                      " (Streak: " + str(stats["streak"]) + "d, Rate: " + str(stats["rate"]) + "%)")
            print("")
        else:
            print("Keine Habits angelegt. Starte Onboarding Session 3.\n")
        return True
    if lower.startswith("training") or lower.startswith("habit "):
        query = lower.replace("training", "training").replace("gemacht", "").replace("erledigt", "").strip()
        if "habit " in lower:
            query = lower.split("habit ", 1)[1].replace("erledigt", "").replace("gemacht", "").strip()
        h = find_habit(query) if query else find_habit("training")
        if h:
            log_habit(h["id"])
            stats = get_habit_stats(h["id"])
            print(h["name"] + " geloggt. Streak: " + str(stats["streak"]) + " Tage.\n")
        else:
            print("Habit nicht gefunden.\n")
        return True

    # Skills + Stats
    if lower == "skills":
        sk = list_skills()
        if sk:
            print("\nVerfuegbare Skills (" + str(len(sk)) + "):")
            current_cat = ""
            for s in sk:
                if s["category"] != current_cat:
                    current_cat = s["category"]
                    print("  " + current_cat.upper() + ":")
                print("    " + s["name"] + " (" + str(s["usage_count"]) + "x genutzt)")
            print("")
        return True
    if lower in ("stats", "fortschritt"):
        habits = list_habits()
        if habits:
            print("\nFortschritt (14 Tage):")
            for h in habits:
                s = get_habit_stats(h["id"])
                bar = "=" * (s["rate"] // 10) + "-" * (10 - s["rate"] // 10)
                print("  " + h["name"] + ": [" + bar + "] " + str(s["rate"]) +
                      "% (Streak: " + str(s["streak"]) + "d)")
            print("")
        done_today = len(get_tasks_completed_today())
        open_tasks = len(list_tasks(status="open"))
        print("  Tasks heute: " + str(done_today) + " erledigt, " + str(open_tasks) + " offen\n")
        return True

    return False
