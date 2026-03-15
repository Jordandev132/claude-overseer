"""Ingest — pull all current Brotherhood data for Claude's reasoning."""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from config import (
    VIPER_LEADS_FILE, THOR_QUEUE_FILE, CLIENTS_FILE, COSTS_FILE,
    CONTENT_METRICS_FILE, HEALTH_STATUS_FILE, AGENT_STATUS_FILE,
    GIG_INBOX_FILE, DIRECTIVES_FILE, DAILY_COST_ALERT_USD,
    MAX_STATUS_FILE, MAX_QUEUE_FILE, SERVICES_FILE, ONBOARDING_FILE,
    PROFILES_FILE, FINANCES_FILE, JORDAN_TASKS_FILE, PROPOSALS_DIR,
)

log = logging.getLogger("overseer.ingest")

# Robotox data paths (on Pro these are under ~/sentinel/)
_SENTINEL_DIR = Path.home() / "sentinel"
_SENTINEL_STATUS = _SENTINEL_DIR / "data" / "status.json"
_SENTINEL_ALERTS = _SENTINEL_DIR / "data" / "alerts.json"


def _read_json(path: Path) -> dict | list | None:
    """Read a JSON file, return None if missing or corrupt."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception as e:
        log.warning("Failed to read %s: %s", path.name, e)
        return None


def _build_health_status() -> dict | None:
    """Build health_status.json from Robotox's sentinel files.

    Reads sentinel/data/status.json + alerts.json and produces
    the simplified format Claude expects.
    """
    status = _read_json(_SENTINEL_STATUS)
    if not status:
        return None

    alerts = _read_json(_SENTINEL_ALERTS) or []

    # Build per-agent status from Robotox's scan data
    agents = {}
    agent_details = status.get("agent_details", {})
    for name, detail in agent_details.items():
        agents[name] = {
            "status": "healthy" if detail.get("running") else "down",
            "last_seen": detail.get("last_check", ""),
        }

    # If no agent_details, fall back to summary counts
    if not agents:
        online = status.get("agents_online", 0)
        total = status.get("total_agents", 0)
        agents = {"summary": f"{online}/{total} agents online"}

    # Recent critical alerts
    recent_alerts = []
    now = time.time()
    for alert in (alerts[-10:] if isinstance(alerts, list) else []):
        ts = alert.get("timestamp", 0)
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts).timestamp()
            except Exception:
                ts = 0
        if now - ts < 3600:  # last hour
            recent_alerts.append(alert.get("message", str(alert)))

    health = {
        "last_check": status.get("last_scan", ""),
        "overall_status": "healthy" if status.get("active_issues", 0) == 0 else "degraded",
        "agents_online": status.get("agents_online", 0),
        "total_agents": status.get("agents_total", status.get("total_agents", 0)),
        "active_issues": status.get("active_issues", 0),
        "agents": agents,
        "recent_alerts": recent_alerts,
        "costs": {
            "alert_threshold": DAILY_COST_ALERT_USD,
        },
        "system": status.get("system", {}),
    }

    # Write to health_status.json so dashboard can also read it
    HEALTH_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    HEALTH_STATUS_FILE.write_text(json.dumps(health, indent=2))

    return health


def _list_proposals() -> list[dict] | None:
    """List recent proposals from Thor's proposal generator."""
    proposals = []
    for f in sorted(PROPOSALS_DIR.glob("proposal_*.md"), reverse=True)[:10]:
        st = f.stat()
        proposals.append({
            "filename": f.name,
            "size": st.st_size,
            "created": datetime.fromtimestamp(st.st_ctime, tz=timezone.utc).isoformat(),
        })
    return proposals or None


def pull_all() -> dict:
    """Pull all data sources into a single dict for prompt building.

    Missing files are represented as None — prompt.py handles them.
    """
    data = {
        "viper_leads": _read_json(VIPER_LEADS_FILE),
        "thor_queue": _read_json(THOR_QUEUE_FILE),
        "clients": _read_json(CLIENTS_FILE),
        "costs": _read_json(COSTS_FILE),
        "content_metrics": _read_json(CONTENT_METRICS_FILE),
        "health_status": _build_health_status(),
        "agent_status": _read_json(AGENT_STATUS_FILE),
        "gig_inbox": _read_json(GIG_INBOX_FILE),
        "jordan_directives": _read_json(DIRECTIVES_FILE),
        "max_status": _read_json(MAX_STATUS_FILE),
        "max_queue": _read_json(MAX_QUEUE_FILE),
        "services": _read_json(SERVICES_FILE),
        "onboarding_sop": _read_json(ONBOARDING_FILE),
        "profiles": _read_json(PROFILES_FILE),
        "jordan_tasks": _read_json(JORDAN_TASKS_FILE),
        "finances": _read_json(FINANCES_FILE),
        "proposals": _list_proposals(),
    }

    # Count what we got
    present = sum(1 for v in data.values() if v is not None)
    log.info("Ingested %d/%d data sources", present, len(data))

    return data
