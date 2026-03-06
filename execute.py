"""Execute Claude's decisions — write configs, send alerts, update status.

Uses shared telegram_notify for all TG messages.
RULE: 1 message per topic. Max 2-3 lines. No spam.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from config import (
    STATUS_FILE, THOR_QUEUE_FILE, AGENT_STATUS_FILE,
)
from schemas import CycleDecision, Memory

sys.path.insert(0, str(Path.home() / "shared"))
from telegram_notify import (
    notify, notify_alert, notify_question, notify_claude_cycle,
    NotifyType, Urgency,
)

log = logging.getLogger("overseer.execute")


def _update_json(path, updater):
    """Read JSON file, apply updater function, write back."""
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text())
        except Exception:
            pass
    updater(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def run(decision: CycleDecision, mem: Memory) -> list[str]:
    """Execute a cycle's decisions. Returns list of actions taken."""
    actions_taken = []
    tg_sent = 0  # Track how many TG messages we've sent

    # 1. Agent actions (pause/resume)
    for agent, action in decision.agent_actions.items():
        if action in ("pause", "resume"):
            log.info("Agent action: %s -> %s", agent, action)
            _update_json(AGENT_STATUS_FILE, lambda d: d.update(
                {agent: {"status": "paused" if action == "pause" else "active",
                         "updated": datetime.now(timezone.utc).isoformat()}}
            ))
            actions_taken.append(f"{agent}:{action}")
        else:
            log.info("Agent directive: %s -> %s", agent, action)
            actions_taken.append(f"{agent}:{action}")

    # 2. Task assignments -> append to Thor queue (NO TG per task — digest only)
    if decision.task_assignments:
        def _add_tasks(data):
            tasks = data.get("tasks", [])
            for ta in decision.task_assignments:
                tasks.append({
                    "agent": ta.agent,
                    "task": ta.task,
                    "priority": ta.priority,
                    "status": "pending",
                    "assigned_by": "claude_overseer",
                    "assigned_at": datetime.now(timezone.utc).isoformat(),
                })
            data["tasks"] = tasks

        _update_json(THOR_QUEUE_FILE, _add_tasks)
        for ta in decision.task_assignments:
            actions_taken.append(f"task:{ta.agent}:{ta.task[:50]}")
            log.info("Task assigned: %s -> %s (P%d)", ta.agent, ta.task[:60], ta.priority)

    # 3. Questions ABSORB alerts on the same topic.
    #    If there's a question, that IS the notification. Don't also send an alert.
    #    Questions are actionable. Alerts are FYI. Question > Alert.
    question_topics = set()
    for q in decision.questions_for_jordan:
        notify_question(q[:250])
        actions_taken.append(f"question:{q[:50]}")
        # Extract keywords to match against alerts
        question_topics.update(q.lower().split()[:10])
        tg_sent += 1

    # 4. Alerts -> only send if NOT already covered by a question
    for alert in decision.alerts:
        alert_words = set(alert.lower().split()[:10])
        overlap = alert_words & question_topics
        if len(overlap) >= 3:
            # Already covered by a question — skip
            log.info("Alert absorbed by question: %s", alert[:60])
            actions_taken.append(f"alert_absorbed:{alert[:50]}")
        else:
            notify_alert("Claude", alert[:200])
            actions_taken.append(f"alert:{alert[:50]}")
            tg_sent += 1

    # 5. Content directives -> logged only (no TG)
    if decision.content_directives:
        for cd in decision.content_directives:
            log.info("Content: %s -> %s on %s (%s)",
                     cd.agent, cd.topic[:40], cd.platform, cd.angle[:30])
            actions_taken.append(f"content:{cd.agent}:{cd.platform}")

    # 6. Cycle summary — ONLY if no other TG messages were sent this cycle.
    #    If questions/alerts already went out, don't spam with a summary too.
    if tg_sent == 0:
        # Quiet cycle — send a brief 1-liner
        summary = decision.reasoning[:150]
        notify_claude_cycle(f"{summary}")
        tg_sent += 1

    # 7. Write claude_status.json (dashboard has full details)
    status = {
        "last_cycle": decision.cycle_id,
        "reasoning": decision.reasoning,
        "agent_actions": decision.agent_actions,
        "task_count": len(decision.task_assignments),
        "alert_count": len(decision.alerts),
        "question_count": len(decision.questions_for_jordan),
        "content_directives": [cd.model_dump() for cd in decision.content_directives],
        "experiments": [e.model_dump() for e in decision.experiments],
        "questions_for_jordan": decision.questions_for_jordan,
        "actions_taken": actions_taken,
    }
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(status, indent=2))

    log.info("Executed %d actions, %d TG messages", len(actions_taken), tg_sent)
    return actions_taken
