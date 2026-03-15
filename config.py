"""Claude Overseer configuration — loads from environment / .env."""

import os
from pathlib import Path

# ── Paths ──
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "claude_log"

# Also check polymarket-bot .env for shared keys
_PM_ENV = Path.home() / "polymarket-bot" / ".env"
_SHELBY_ENV = Path.home() / "shelby" / ".env"


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader — no external dependency."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = val


# Load envs (Shelby has TG creds, polymarket-bot has Anthropic key)
_load_dotenv(_PM_ENV)
_load_dotenv(_SHELBY_ENV)

# ── API Keys ──
ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.environ.get("TELEGRAM_CHAT_ID", "")

# ── Model ──
MODEL: str = os.environ.get("CLAUDE_OVERSEER_MODEL", "claude-sonnet-4-20250514")
MAX_TOKENS: int = int(os.environ.get("CLAUDE_OVERSEER_MAX_TOKENS", "4096"))

# ── Loop ──
LOOP_INTERVAL_S: int = int(os.environ.get("CLAUDE_OVERSEER_INTERVAL_S", "7200"))  # 2h
RETRY_DELAY_S: int = 60

# ── Cost guard ──
DAILY_COST_ALERT_USD: float = float(os.environ.get("CLAUDE_OVERSEER_COST_ALERT", "10.0"))

# ── Memory ──
MAX_DECISIONS_KEPT: int = 10
MEMORY_FILE = DATA_DIR / "claude_memory.json"
STATUS_FILE = DATA_DIR / "claude_status.json"
DIRECTIVES_FILE = DATA_DIR / "claude.json"

# ── External data files Claude reads ──
VIPER_LEADS_FILE = DATA_DIR / "viper_leads.json"
THOR_QUEUE_FILE = DATA_DIR / "thor_queue.json"
CLIENTS_FILE = DATA_DIR / "clients.json"
COSTS_FILE = DATA_DIR / "costs.json"
CONTENT_METRICS_FILE = DATA_DIR / "content_metrics.json"
HEALTH_STATUS_FILE = DATA_DIR / "health_status.json"
AGENT_STATUS_FILE = DATA_DIR / "agent_status.json"
GIG_INBOX_FILE = DATA_DIR / "gig_inbox.json"
MAX_STATUS_FILE = Path.home() / "max" / "data" / "max_status.json"
MAX_QUEUE_FILE = Path.home() / "max" / "data" / "content_queue.json"
SERVICES_FILE = DATA_DIR / "services.json"
ONBOARDING_FILE = DATA_DIR / "onboarding_sop.json"
PROFILES_FILE = DATA_DIR / "profiles.json"
FINANCES_FILE = DATA_DIR / "finances.json"
JORDAN_TASKS_FILE = Path.home() / "polymarket-bot" / "data" / "jordan_tasks.json"
PROPOSALS_DIR = Path.home() / "thor" / "data" / "proposals"

# ── Permissions (what Claude can do autonomously) ──
AUTO_PERMISSIONS = {
    "pause_agent",
    "resume_agent",
    "assign_thor_task",
    "set_viper_priority",
    "push_content_idea",
    "add_remove_workflow",
    "start_stop_experiment",
    "alert_jordan",
}

JORDAN_APPROVAL_REQUIRED = {
    "delete_agent",
    "spend_money",
    "change_bankroll",
    "modify_pricing",
    "contact_client",
}
