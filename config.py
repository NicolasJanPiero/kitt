import os

# Pfade
KITT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(KITT_DIR, "kitt.db")
WORKSPACE = os.path.expanduser("~/agent-workspace")
LOG_DIR = os.path.join(WORKSPACE, "logs")
ALLOWED_DIRS = [WORKSPACE]
SOUL_PATH = os.path.join(KITT_DIR, "SOUL.md")

# Ollama (lokal, fuer persoenliche Daten)
OLLAMA_MODEL = "llama3.2:3b"

# Anthropic API (fuer Arbeits-Tasks, Skills, Coaching)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

# sim.ai-claw Bridge (fuer Kundendaten)
SIMAI_WEBHOOK_URL = os.environ.get("SIMAI_WEBHOOK_URL", "")
SIMAI_API_KEY = os.environ.get("SIMAI_API_KEY", "")

# Datenklassifizierung fuer LLM-Routing
PERSONAL_KEYWORDS = [
    "training", "gym", "sport", "schlaf", "gesundheit", "ernaehrung",
    "meditation", "gewohnheit", "habit", "wasser", "feierabend",
    "muede", "energie", "stimmung", "mood"
]

SIMAI_KEYWORDS = [
    "email", "e-mail", "mail", "outlook",
    "linkedin", "content",
    "kunde", "crm", "brevo", "pipeline",
    "workflow", "sim.ai", "simai"
]

# Shell-Blocklist
BLOCKED_COMMANDS = [
    "rm -rf /", "rm -rf ~", "sudo", "chmod 777", "curl | sh",
    "wget | sh", "mv /", "cp /etc", "cat /etc/shadow",
    "cat /etc/passwd", "pkill", "killall", "> /dev/sda",
    "mkfs", "dd if=", ":(){ :|:& };:"
]
