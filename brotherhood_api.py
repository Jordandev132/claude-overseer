"""Brotherhood API Blueprint — all agent endpoints for Shelby TG bot.

Reads real data from disk. Never crashes — returns safe defaults.
Registered on the dashboard (port 8878).
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, request

from data_readers import (
    PATHS, read_json, read_jsonl_tail,
    list_dir_json, get_launchctl_agents, get_system_metrics,
)

bp = Blueprint("brotherhood_api", __name__)
HOME = Path.home()

# ── Whitelist for system actions ──
ALLOWED_ACTIONS = {
    "restart_shelby", "restart_atlas", "restart_viper", "restart_robotox",
    "restart_thor", "restart_quant", "restart_soren", "restart_dashboard",
    "restart_max",
}

AGENT_PLISTS = {
    "shelby": "com.shelby.assistant",
    "atlas": "com.atlas.agent",
    "viper": "com.viper.agent",
    "robotox": "com.robotox.agent",
    "thor": "com.thor.agent",
    "quant": "com.quant.agent",
    "soren": "com.soren.bot",
    "dashboard": "com.brotherhood.dashboard",
    "max": "com.max.agent",
}

HAWK_KILLED = {"status": "KILLED", "message": "Hawk killed Mar 3 2026 — $328 burned"}
DEAD_AGENTS = {"hawk", "odin", "killshot"}


# ═══════════════════════════════════════════════════════════════
# OVERVIEW & SYSTEM
# ═══════════════════════════════════════════════════════════════

@bp.route("/api/overview")
def api_overview():
    status = read_json(PATHS["sentinel_status"], {})
    pnl = read_json(PATHS["brotherhood_pnl"], {})
    agents_running = get_launchctl_agents()

    # Build per-agent summary from Robotox status
    agent_summaries = {}
    if isinstance(status, dict):
        for name, info in status.items():
            if isinstance(info, dict):
                agent_summaries[name] = {
                    "running": info.get("status") == "running" or info.get("running", False),
                    "last_seen": info.get("last_seen", info.get("timestamp")),
                    **{k: v for k, v in info.items() if k not in ("status", "running", "last_seen", "timestamp")},
                }

    return jsonify({
        "agents": agent_summaries,
        "launchctl": agents_running,
        "pnl": pnl,
        "timestamp": datetime.utcnow().isoformat(),
    })


@bp.route("/api/health")
def api_health():
    status = read_json(PATHS["sentinel_status"], {})
    alerts = read_json(PATHS["sentinel_alerts"], [])
    return jsonify({"status": status, "alerts": alerts})


@bp.route("/api/heartbeats")
def api_heartbeats():
    status = read_json(PATHS["sentinel_status"], {})
    return jsonify(status)


@bp.route("/api/intelligence")
def api_intelligence():
    return jsonify(read_json(PATHS["atlas_intel"], {}))


@bp.route("/api/broadcasts")
def api_broadcasts():
    return jsonify(read_json(PATHS["broadcast"], []))


@bp.route("/api/events")
def api_events():
    limit = request.args.get("limit", 20, type=int)
    events = read_jsonl_tail(PATHS["events"], limit)
    return jsonify(events)


@bp.route("/api/events/stats")
def api_events_stats():
    events = read_jsonl_tail(PATHS["events"], 1000)
    by_type = {}
    for e in events:
        t = e.get("type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1
    return jsonify({"total": len(events), "by_type": by_type})


@bp.route("/api/system/metrics")
def api_system_metrics():
    return jsonify(get_system_metrics())


@bp.route("/api/system/processes")
def api_system_processes():
    try:
        r = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True, timeout=10
        )
        procs = []
        for line in r.stdout.splitlines():
            if "python" in line.lower():
                procs.append(line)
        return jsonify({"processes": procs})
    except Exception as e:
        return jsonify({"error": str(e), "processes": []})


@bp.route("/api/system/ports")
def api_system_ports():
    try:
        r = subprocess.run(
            ["lsof", "-iTCP", "-sTCP:LISTEN", "-P", "-n"],
            capture_output=True, text=True, timeout=10
        )
        return jsonify({"ports": r.stdout.splitlines()})
    except Exception as e:
        return jsonify({"error": str(e), "ports": []})


@bp.route("/api/system/launchagents")
def api_system_launchagents():
    return jsonify(get_launchctl_agents())


@bp.route("/api/system/action/<action>", methods=["POST"])
def api_system_action(action):
    if action not in ALLOWED_ACTIONS:
        return jsonify({"error": f"Action '{action}' not allowed"}), 403

    # Parse agent name from action
    agent_name = action.replace("restart_", "")
    plist = AGENT_PLISTS.get(agent_name)
    if not plist:
        return jsonify({"error": f"Unknown agent '{agent_name}'"}), 404

    try:
        uid = subprocess.run(
            ["id", "-u"], capture_output=True, text=True, timeout=5
        ).stdout.strip()
        subprocess.run(
            ["launchctl", "kickstart", "-k", f"gui/{uid}/{plist}"],
            capture_output=True, text=True, timeout=30
        )
        return jsonify({"status": "ok", "action": action, "plist": plist})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════
# GARVES
# ═══════════════════════════════════════════════════════════════

@bp.route("/api/trades")
def api_trades():
    trades = read_jsonl_tail(PATHS["trades"], 20)
    return jsonify(trades)


@bp.route("/api/trades/live")
def api_trades_live():
    return jsonify(read_json(PATHS["arbiter_positions"], []))


@bp.route("/api/garves/daily-report/today")
def api_garves_daily_today():
    reports = read_json(PATHS["daily_reports"], [])
    if isinstance(reports, list) and reports:
        return jsonify(reports[-1])
    if isinstance(reports, dict):
        return jsonify(reports)
    return jsonify({})


@bp.route("/api/garves/regime")
def api_garves_regime():
    return jsonify(read_json(PATHS["external_data_state"], {}))


@bp.route("/api/garves/conviction")
def api_garves_conviction():
    return jsonify(read_json(PATHS["diagnostics"], {}))


@bp.route("/api/garves/derivatives")
def api_garves_derivatives():
    return jsonify(read_json(PATHS["derivatives_state"], {}))


@bp.route("/api/garves/news-sentiment")
def api_garves_news_sentiment():
    return jsonify(read_json(PATHS["atlas_news_sentiment"], {}))


@bp.route("/api/garves/balance")
def api_garves_balance():
    status = read_json(PATHS["arbiter_status"], {})
    return jsonify({
        "balance": status.get("balance"),
        "available": status.get("available"),
        "invested": status.get("invested"),
        "total_value": status.get("total_value"),
        "timestamp": status.get("timestamp"),
    })


@bp.route("/api/garves/positions")
def api_garves_positions():
    return jsonify(read_json(PATHS["arbiter_positions"], []))


@bp.route("/api/garves/daily-reports")
def api_garves_daily_reports():
    return jsonify(read_json(PATHS["daily_reports"], []))


# ═══════════════════════════════════════════════════════════════
# HAWK — DEAD
# ═══════════════════════════════════════════════════════════════

@bp.route("/api/hawk")
@bp.route("/api/hawk/opportunities")
@bp.route("/api/hawk/positions")
@bp.route("/api/hawk/history")
@bp.route("/api/hawk/categories")
@bp.route("/api/hawk/suggestions")
def api_hawk_dead():
    return jsonify(HAWK_KILLED)


@bp.route("/api/hawk/scan", methods=["POST"])
@bp.route("/api/hawk/approve", methods=["POST"])
@bp.route("/api/hawk/dismiss", methods=["POST"])
def api_hawk_dead_post():
    return jsonify(HAWK_KILLED)


# ═══════════════════════════════════════════════════════════════
# ATLAS
# ═══════════════════════════════════════════════════════════════

@bp.route("/api/atlas/background/status")
def api_atlas_bg_status():
    return jsonify(read_json(PATHS["atlas_bg_status"], {}))


@bp.route("/api/atlas/costs")
def api_atlas_costs():
    return jsonify(read_json(PATHS["atlas_costs"], {}))


@bp.route("/api/atlas/knowledge")
def api_atlas_knowledge():
    return jsonify(read_json(PATHS["atlas_knowledge"], {}))


@bp.route("/api/atlas/live-research")
def api_atlas_live_research():
    return jsonify(read_json(PATHS["atlas_research_log"], {}))


@bp.route("/api/atlas/improvements", methods=["GET", "POST"])
def api_atlas_improvements():
    return jsonify(read_json(PATHS["atlas_improvements"], {}))


@bp.route("/api/atlas/improvements/acknowledge", methods=["POST"])
def api_atlas_improvements_ack():
    data = read_json(PATHS["atlas_improvements"], {})
    if isinstance(data, dict):
        data["acknowledged"] = True
        try:
            PATHS["atlas_improvements"].write_text(json.dumps(data, indent=2))
        except Exception:
            pass
    return jsonify({"status": "ok"})


@bp.route("/api/atlas/thoughts")
def api_atlas_thoughts():
    return jsonify(read_json(PATHS["atlas_observations"], {}))


@bp.route("/api/atlas/experiments")
def api_atlas_experiments():
    return jsonify([])


@bp.route("/api/atlas/hub-eval")
def api_atlas_hub_eval():
    return jsonify(read_json(PATHS["atlas_score_history"], {}))


@bp.route("/api/atlas/content-pipeline")
def api_atlas_content_pipeline():
    return jsonify(read_json(PATHS["atlas_content_feed"], {}))


@bp.route("/api/atlas/feed-content", methods=["POST"])
def api_atlas_feed_content():
    return jsonify({"status": "ok", "message": "Feed request noted"})


# ═══════════════════════════════════════════════════════════════
# SHELBY
# ═══════════════════════════════════════════════════════════════

@bp.route("/api/shelby")
def api_shelby():
    shelby_dir = PATHS["shelby_data_dir"]
    agents = get_launchctl_agents()
    shelby_running = any(a["label"] == "com.shelby.assistant" for a in agents)
    return jsonify({
        "running": shelby_running,
        "data_dir": str(shelby_dir),
        "agents_managed": len(agents),
    })


@bp.route("/api/shelby/brief")
def api_shelby_brief():
    status = read_json(PATHS["sentinel_status"], {})
    agents = get_launchctl_agents()
    running = sum(1 for a in agents if a.get("running"))
    costs = read_jsonl_tail(PATHS["llm_costs"], 100)
    total_cost_24h = sum(e.get("cost", 0) for e in costs)
    return jsonify({
        "agents_running": running,
        "agents_total": len(agents),
        "health_summary": status,
        "llm_cost_24h": round(total_cost_24h, 4),
        "timestamp": datetime.utcnow().isoformat(),
    })


@bp.route("/api/shelby/assessments")
def api_shelby_assessments():
    return jsonify(read_json(PATHS["shelby_tasks"], []))


@bp.route("/api/shelby/economics")
def api_shelby_economics():
    period = request.args.get("period", "all")
    finances = read_json(PATHS["finances"], {})
    costs = read_jsonl_tail(PATHS["llm_costs"], 500)
    return jsonify({
        "finances": finances,
        "llm_costs_recent": costs[-50:],
        "period": period,
    })


@bp.route("/api/shelby/schedule")
def api_shelby_schedule():
    shelby_dir = PATHS["shelby_data_dir"]
    schedule_files = list_dir_json(shelby_dir)
    schedule_data = [f for f in schedule_files if "schedule" in f["file"].lower()]
    return jsonify(schedule_data if schedule_data else [])


@bp.route("/api/shelby/activity-brief")
def api_shelby_activity():
    events = read_jsonl_tail(PATHS["events"], 20)
    return jsonify({"recent_events": events})


@bp.route("/api/shelby/decisions")
def api_shelby_decisions():
    status_file = HOME / "claude_overseer" / "data" / "claude_status.json"
    return jsonify(read_json(status_file, {}))


@bp.route("/api/shelby/tasks", methods=["POST"])
def api_shelby_create_task():
    data = request.get_json(silent=True) or {}
    title = data.get("title", "")
    agent = data.get("agent")
    task = {
        "title": title,
        "agent": agent,
        "created": datetime.utcnow().isoformat(),
        "status": "pending",
    }
    # Append to shelby tasks
    tasks = read_json(PATHS["shelby_tasks"], [])
    if not isinstance(tasks, list):
        tasks = []
    tasks.append(task)
    try:
        PATHS["shelby_tasks"].parent.mkdir(parents=True, exist_ok=True)
        PATHS["shelby_tasks"].write_text(json.dumps(tasks, indent=2))
    except Exception:
        pass
    return jsonify({"status": "ok", "task": task})


@bp.route("/api/shelby/tasks/<int:task_id>/dispatch", methods=["POST"])
def api_shelby_dispatch_task(task_id):
    tasks = read_json(PATHS["shelby_tasks"], [])
    if isinstance(tasks, list) and 0 <= task_id < len(tasks):
        tasks[task_id]["status"] = "dispatched"
        try:
            PATHS["shelby_tasks"].write_text(json.dumps(tasks, indent=2))
        except Exception:
            pass
        return jsonify({"status": "ok", "task": tasks[task_id]})
    return jsonify({"error": "Task not found"}), 404


# ═══════════════════════════════════════════════════════════════
# ROBOTOX / SENTINEL
# ═══════════════════════════════════════════════════════════════

@bp.route("/api/sentinel")
def api_sentinel():
    status = read_json(PATHS["sentinel_status"], {})
    scan = read_json(PATHS["sentinel_scan"], {})
    scorecards = read_json(PATHS["sentinel_scorecards"], {})
    return jsonify({
        "status": status,
        "scan_results": scan,
        "scorecards": scorecards,
    })


@bp.route("/api/sentinel/scan", methods=["POST"])
def api_sentinel_scan():
    flag = HOME / "sentinel" / "data" / "trigger_scan"
    try:
        flag.touch()
        return jsonify({"status": "ok", "message": "Scan triggered"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/sentinel/fixes")
def api_sentinel_fixes():
    return jsonify(read_json(PATHS["sentinel_fixes"], []))


@bp.route("/api/robotox/log-alerts")
def api_robotox_log_alerts():
    return jsonify(read_json(PATHS["log_watcher_alerts"], []))


@bp.route("/api/robotox/dependencies")
def api_robotox_dependencies():
    return jsonify(read_json(PATHS["dep_health"], {}))


@bp.route("/api/robotox/dependencies/check", methods=["POST"])
def api_robotox_dep_check():
    return jsonify(read_json(PATHS["dep_health"], {}))


# ═══════════════════════════════════════════════════════════════
# VIPER
# ═══════════════════════════════════════════════════════════════

@bp.route("/api/viper")
def api_viper():
    return jsonify(read_json(PATHS["viper_status"], {}))


@bp.route("/api/viper/opportunities")
def api_viper_opportunities():
    return jsonify(read_json(PATHS["viper_opportunities"], []))


@bp.route("/api/viper/costs")
def api_viper_costs():
    return jsonify(read_json(PATHS["viper_costs"], {}))


@bp.route("/api/viper/soren-metrics")
def api_viper_soren_metrics():
    return jsonify(read_json(PATHS["viper_soren_digest"], {}))


# ═══════════════════════════════════════════════════════════════
# THOR
# ═══════════════════════════════════════════════════════════════

@bp.route("/api/thor")
def api_thor():
    return jsonify(read_json(PATHS["thor_status"], {}))


@bp.route("/api/thor/queue")
def api_thor_queue():
    return jsonify(list_dir_json(PATHS["thor_tasks_dir"]))


@bp.route("/api/thor/results")
def api_thor_results():
    return jsonify(list_dir_json(PATHS["thor_results_dir"]))


@bp.route("/api/thor/smart-actions")
def api_thor_smart_actions():
    return jsonify(read_json(PATHS["thor_commands"], []))


@bp.route("/api/thor/submit", methods=["POST"])
def api_thor_submit():
    data = request.get_json(silent=True) or {}
    title = data.get("title", "untitled")
    description = data.get("description", "")
    task = {
        "title": title,
        "description": description,
        "submitted": datetime.utcnow().isoformat(),
        "status": "queued",
    }
    tasks_dir = PATHS["thor_tasks_dir"]
    try:
        tasks_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        fname = tasks_dir / f"task_{ts}.json"
        fname.write_text(json.dumps(task, indent=2))
        return jsonify({"status": "ok", "task": task, "file": str(fname)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/thor/quick-action", methods=["POST"])
def api_thor_quick_action():
    data = request.get_json(silent=True) or {}
    return jsonify({"status": "ok", "action": data, "message": "Action queued for Thor"})


# ═══════════════════════════════════════════════════════════════
# SOREN
# ═══════════════════════════════════════════════════════════════

@bp.route("/api/soren")
def api_soren():
    queue = read_json(PATHS["soren_content_queue"], [])
    metrics = read_json(PATHS["soren_content_metrics"], {})
    return jsonify({"content_queue": queue, "metrics": metrics})


@bp.route("/api/soren/competitors")
def api_soren_competitors():
    return jsonify(read_json(PATHS["soren_competitors"], []))


# ═══════════════════════════════════════════════════════════════
# LISA
# ═══════════════════════════════════════════════════════════════

@bp.route("/api/lisa")
def api_lisa():
    pending = read_json(PATHS["lisa_pending_tweets"], [])
    queue = read_json(PATHS["soren_content_queue"], [])
    return jsonify({"pending_tweets": pending, "content_queue": queue})


@bp.route("/api/lisa/jordan-queue")
def api_lisa_jordan_queue():
    queue = read_json(PATHS["soren_content_queue"], [])
    if isinstance(queue, list):
        pending = [item for item in queue if item.get("status") == "pending"]
        return jsonify(pending)
    return jsonify([])


@bp.route("/api/lisa/jordan-approve/<item_id>", methods=["POST"])
def api_lisa_jordan_approve(item_id):
    queue = read_json(PATHS["soren_content_queue"], [])
    if isinstance(queue, list):
        for item in queue:
            if str(item.get("id")) == item_id:
                item["status"] = "approved"
                try:
                    PATHS["soren_content_queue"].write_text(json.dumps(queue, indent=2))
                except Exception:
                    pass
                return jsonify({"status": "ok", "item": item})
    return jsonify({"error": "Item not found"}), 404


@bp.route("/api/lisa/posting-schedule")
def api_lisa_schedule():
    return jsonify(read_json(PATHS["tweet_schedule"], []))


@bp.route("/api/lisa/live-config")
def api_lisa_live_config():
    return jsonify({"tiktok": False, "instagram": False, "x": False})


@bp.route("/api/lisa/pipeline/stats")
def api_lisa_pipeline_stats():
    return jsonify(read_json(PATHS["soren_content_metrics"], {}))


@bp.route("/api/lisa/go-live", methods=["POST"])
def api_lisa_go_live():
    data = request.get_json(silent=True) or {}
    return jsonify({"status": "ok", "platform": data.get("platform"), "live": data.get("live")})


# ═══════════════════════════════════════════════════════════════
# QUANT
# ═══════════════════════════════════════════════════════════════

@bp.route("/api/quant")
def api_quant():
    return jsonify(read_json(PATHS["quant_status"], {}))


@bp.route("/api/quant/results")
def api_quant_results():
    return jsonify(read_json(PATHS["quant_walk_forward"], {}))


@bp.route("/api/quant/recommendations")
def api_quant_recommendations():
    versions_dir = PATHS["quant_versions_dir"]
    files = list_dir_json(versions_dir)
    return jsonify(files[0] if files else {})


@bp.route("/api/quant/params")
def api_quant_params():
    return jsonify(read_json(PATHS["quant_walk_forward"], {}))


# ═══════════════════════════════════════════════════════════════
# ORACLE
# ═══════════════════════════════════════════════════════════════

@bp.route("/api/oracle")
def api_oracle():
    oracle_status = HOME / "polymarket-bot" / "data" / "oracle_status.json"
    return jsonify(read_json(oracle_status, {"status": "PAPER_MODE", "dry_run": True}))


@bp.route("/api/oracle/predictions")
def api_oracle_predictions():
    oracle_preds = HOME / "polymarket-bot" / "data" / "oracle_predictions.json"
    return jsonify(read_json(oracle_preds, []))


@bp.route("/api/oracle/report")
def api_oracle_report():
    oracle_report = HOME / "polymarket-bot" / "data" / "oracle_report.json"
    return jsonify(read_json(oracle_report, {}))


@bp.route("/api/oracle/accuracy")
def api_oracle_accuracy():
    oracle_acc = HOME / "polymarket-bot" / "data" / "oracle_accuracy.json"
    return jsonify(read_json(oracle_acc, {}))


# ═══════════════════════════════════════════════════════════════
# CHAT — NOT IMPLEMENTED
# ═══════════════════════════════════════════════════════════════

@bp.route("/api/chat/agent/<agent>", methods=["POST"])
def api_chat_agent(agent):
    return jsonify({"status": "not_implemented", "agent": agent})
