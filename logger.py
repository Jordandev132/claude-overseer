"""Audit logger — one JSON file per cycle."""

import json
import logging
from datetime import datetime, timezone

from config import LOG_DIR
from schemas import CycleDecision

log = logging.getLogger("overseer.logger")


def write_cycle_log(
    decision: CycleDecision,
    ingested_summary: dict,
    actions_taken: list[str],
    api_latency_ms: int = 0,
) -> str:
    """Write a full audit log for this cycle. Returns the log file path."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    filename = f"claude_log_{now.strftime('%Y-%m-%dT%H-%M')}.json"
    path = LOG_DIR / filename

    entry = {
        "timestamp": now.isoformat(),
        "cycle_id": decision.cycle_id,
        "api_latency_ms": api_latency_ms,
        "input_summary": {
            k: ("present" if v is not None else "missing")
            for k, v in ingested_summary.items()
        },
        "reasoning": decision.reasoning,
        "memory_context": decision.memory_context,
        "decisions": decision.model_dump(),
        "actions_taken": actions_taken,
    }

    path.write_text(json.dumps(entry, indent=2))
    log.info("Cycle log written: %s", filename)
    return str(path)
