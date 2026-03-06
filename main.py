#!/usr/bin/env python3
"""Claude Overseer — The True Godfather Loop.

recall → ingest → call Claude API → execute → save → log
Runs every 1-4 hours. This is Claude's brain.
"""

import json
import logging
import sys
import time
from datetime import datetime, timezone

from pathlib import Path

import anthropic

sys.path.insert(0, str(Path.home() / "shared"))
from telegram_notify import notify_alert

import config
import ingest
import memory as mem_mod
import prompt as prompt_mod
import execute as exec_mod
import logger as log_mod
from schemas import CycleDecision

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.DATA_DIR / "overseer.log"),
    ],
)
log = logging.getLogger("overseer")


def _call_claude(system: str, user: str) -> tuple[str, int]:
    """Call Claude API. Returns (response_text, latency_ms)."""
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    t0 = time.monotonic()
    response = client.messages.create(
        model=config.MODEL,
        max_tokens=config.MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    latency_ms = int((time.monotonic() - t0) * 1000)
    text = response.content[0].text
    return text, latency_ms


def _parse_decision(raw: str) -> CycleDecision:
    """Parse Claude's JSON response into CycleDecision."""
    # Strip markdown fences if present
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last fence lines
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    data = json.loads(text)
    return CycleDecision.model_validate(data)


def _send_failure_alert(error: str) -> None:
    """Alert Jordan that the loop failed."""
    notify_alert("Claude Overseer", f"FAILED — {error[:150]}", "Check logs.")


def run_cycle() -> bool:
    """Run one full oversight cycle. Returns True on success."""
    cycle_id = datetime.now(timezone.utc).isoformat()
    log.info("=== Cycle %s ===", cycle_id)

    # 1. RECALL — load persistent memory
    mem = mem_mod.load()
    log.info("Memory loaded: %d past decisions, %d experiments",
             len(mem.last_10_decisions), len(mem.active_experiments))

    # 2. INGEST — pull all current data
    ingested = ingest.pull_all()

    # 3. BUILD PROMPT
    system = prompt_mod.SYSTEM_PROMPT
    user = prompt_mod.build_user_prompt(mem, ingested)

    # 4. CALL CLAUDE
    raw_response, latency_ms = _call_claude(system, user)
    log.info("Claude responded in %dms (%d chars)", latency_ms, len(raw_response))

    # 5. PARSE
    decision = _parse_decision(raw_response)
    decision.cycle_id = cycle_id
    log.info("Decision: %d agent_actions, %d tasks, %d alerts, %d questions",
             len(decision.agent_actions), len(decision.task_assignments),
             len(decision.alerts), len(decision.questions_for_jordan))

    # 6. EXECUTE
    actions_taken = exec_mod.run(decision, mem)

    # 7. SAVE — update persistent memory
    mem_mod.save(mem, decision.reasoning[:200])

    # 8. LOG — full audit trail
    log_mod.write_cycle_log(decision, ingested, actions_taken, latency_ms)

    log.info("Cycle complete: %d actions taken", len(actions_taken))
    return True


def main():
    """Main loop — run cycle every LOOP_INTERVAL_S."""
    log.info("Claude Overseer starting — model=%s, interval=%ds",
             config.MODEL, config.LOOP_INTERVAL_S)

    # Ensure data directories exist
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        try:
            run_cycle()
        except json.JSONDecodeError as e:
            log.error("Claude returned invalid JSON: %s", e)
            _send_failure_alert(f"Invalid JSON from Claude: {e}")
        except anthropic.APIError as e:
            log.error("Claude API error: %s", e)
            # Retry once after delay
            log.info("Retrying in %ds...", config.RETRY_DELAY_S)
            time.sleep(config.RETRY_DELAY_S)
            try:
                run_cycle()
            except Exception as e2:
                log.error("Retry also failed: %s", e2)
                _send_failure_alert(f"Claude API failed 2x: {e2}")
        except Exception as e:
            log.error("Unexpected error: %s", e, exc_info=True)
            _send_failure_alert(f"Overseer error: {e}")

        log.info("Sleeping %ds until next cycle...", config.LOOP_INTERVAL_S)
        time.sleep(config.LOOP_INTERVAL_S)


if __name__ == "__main__":
    # Support --once flag for testing
    if "--once" in sys.argv:
        log.info("Running single cycle (--once)")
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            run_cycle()
        except Exception as e:
            log.error("Cycle failed: %s", e, exc_info=True)
            sys.exit(1)
    else:
        main()
