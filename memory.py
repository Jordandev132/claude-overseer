"""Persistent memory — Claude's brain between loops."""

import json
import logging
from datetime import datetime, timezone

from config import MEMORY_FILE, MAX_DECISIONS_KEPT
from schemas import Memory, DecisionSummary

log = logging.getLogger("overseer.memory")


def load() -> Memory:
    """Load memory from disk. Returns empty Memory if file missing."""
    if not MEMORY_FILE.exists():
        log.info("No memory file — starting fresh")
        return Memory()
    try:
        raw = json.loads(MEMORY_FILE.read_text())
        return Memory.model_validate(raw)
    except Exception as e:
        log.warning("Memory load error (starting fresh): %s", e)
        return Memory()


def save(mem: Memory, cycle_summary: str) -> None:
    """Append decision summary and persist to disk."""
    now = datetime.now(timezone.utc).isoformat()
    mem.last_updated = now

    mem.last_10_decisions.append(
        DecisionSummary(cycle=now, summary=cycle_summary, outcome_pending=True)
    )

    # Prune to last N decisions
    if len(mem.last_10_decisions) > MAX_DECISIONS_KEPT:
        mem.last_10_decisions = mem.last_10_decisions[-MAX_DECISIONS_KEPT:]

    # Prune completed experiments
    mem.active_experiments = [
        e for e in mem.active_experiments if e.status == "active"
    ]

    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(mem.model_dump_json(indent=2))
    log.info("Memory saved (%d decisions, %d experiments)",
             len(mem.last_10_decisions), len(mem.active_experiments))
