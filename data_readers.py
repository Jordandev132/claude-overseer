"""Safe data readers for Brotherhood API — never crashes, always returns defaults."""

import json
import subprocess
from pathlib import Path

HOME = Path.home()

# ── Path Registry ──
PATHS = {
    # Sentinel / Robotox
    "sentinel_status": HOME / "sentinel" / "data" / "status.json",
    "sentinel_alerts": HOME / "sentinel" / "data" / "alerts.json",
    "sentinel_scan": HOME / "sentinel" / "data" / "scan_results.json",
    "sentinel_scorecards": HOME / "sentinel" / "data" / "scorecards.json",
    "sentinel_fixes": HOME / "sentinel" / "data" / "fix_log.json",
    "log_watcher_alerts": HOME / "sentinel" / "data" / "log_watcher_alerts.json",
    "dep_health": HOME / "sentinel" / "data" / "dep_health.json",
    # Polymarket-bot (Garves, Hawk, Viper, Quant, Oracle)
    "trades": HOME / "polymarket-bot" / "data" / "trades.jsonl",
    "arbiter_positions": HOME / "polymarket-bot" / "data" / "arbiter_positions.json",
    "daily_reports": HOME / "polymarket-bot" / "data" / "daily_reports.json",
    "external_data_state": HOME / "polymarket-bot" / "data" / "external_data_state.json",
    "diagnostics": HOME / "polymarket-bot" / "data" / "diagnostics.json",
    "derivatives_state": HOME / "polymarket-bot" / "data" / "derivatives_state.json",
    "arbiter_status": HOME / "polymarket-bot" / "data" / "arbiter_status.json",
    "brotherhood_pnl": HOME / "polymarket-bot" / "data" / "brotherhood_pnl.json",
    "broadcast": HOME / "polymarket-bot" / "data" / "broadcast.json",
    "finances": HOME / "polymarket-bot" / "data" / "finances.json",
    "viper_status": HOME / "polymarket-bot" / "data" / "viper_status.json",
    "viper_opportunities": HOME / "polymarket-bot" / "data" / "viper_opportunities.json",
    "viper_costs": HOME / "polymarket-bot" / "data" / "viper_costs.json",
    "viper_soren_digest": HOME / "polymarket-bot" / "data" / "viper_soren_digest.json",
    "quant_status": HOME / "polymarket-bot" / "data" / "quant_status.json",
    "quant_walk_forward": HOME / "polymarket-bot" / "data" / "quant_walk_forward.json",
    "quant_versions_dir": HOME / "polymarket-bot" / "data" / "quant_versions",
    # Atlas
    "atlas_intel": HOME / "atlas" / "data" / "intel.json",
    "atlas_bg_status": HOME / "atlas" / "data" / "background_status.json",
    "atlas_costs": HOME / "atlas" / "data" / "cost_tracker.json",
    "atlas_knowledge": HOME / "atlas" / "data" / "knowledge_base.json",
    "atlas_research_log": HOME / "atlas" / "data" / "research_log.json",
    "atlas_improvements": HOME / "atlas" / "data" / "improvements.json",
    "atlas_observations": HOME / "atlas" / "data" / "observations.json",
    "atlas_score_history": HOME / "atlas" / "data" / "score_history.json",
    "atlas_content_feed": HOME / "atlas" / "data" / "content_feed_log.json",
    "atlas_news_sentiment": HOME / "atlas" / "data" / "news_sentiment.json",
    "soren_competitors": HOME / "atlas" / "data" / "soren_competitors.json",
    "shelby_tasks": HOME / "atlas" / "data" / "shelby_tasks.json",
    # Thor
    "thor_status": HOME / "thor" / "data" / "status.json",
    "thor_tasks_dir": HOME / "thor" / "data" / "tasks",
    "thor_results_dir": HOME / "thor" / "data" / "results",
    "thor_commands": HOME / "thor" / "data" / "brotherhood_commands.json",
    # Soren
    "soren_content_queue": HOME / "soren-content" / "data" / "content_queue.json",
    "soren_content_metrics": HOME / "soren-content" / "data" / "content_metrics.json",
    "lisa_pending_tweets": HOME / "soren-content" / "data" / "lisa_pending_tweets.json",
    "tweet_schedule": HOME / "soren-content" / "data" / "tweet_schedule.json",
    # Shelby
    "shelby_data_dir": HOME / "shelby" / "data",
    # Shared
    "events": HOME / "shared" / "events.jsonl",
    "llm_costs": HOME / "shared" / "llm_costs.jsonl",
}


def read_json(path, default=None):
    """Read a JSON file safely. Returns default on any error."""
    if default is None:
        default = {}
    try:
        p = Path(path)
        if not p.exists():
            return default
        data = json.loads(p.read_text())
        return data
    except Exception:
        return default


def read_jsonl_tail(path, n=20):
    """Read last N lines of a JSONL file. Returns list of dicts."""
    try:
        p = Path(path)
        if not p.exists():
            return []
        lines = p.read_text().strip().splitlines()
        tail = lines[-n:] if len(lines) > n else lines
        results = []
        for line in tail:
            try:
                results.append(json.loads(line))
            except Exception:
                continue
        return results
    except Exception:
        return []


def tail_log(path, n=50):
    """Read last N lines of a log file. Returns list of strings."""
    try:
        p = Path(path)
        if not p.exists():
            return []
        lines = p.read_text().strip().splitlines()
        return lines[-n:] if len(lines) > n else lines
    except Exception:
        return []


def list_dir_json(path):
    """List JSON files in a directory. Returns list of dicts with filename + content."""
    try:
        p = Path(path)
        if not p.is_dir():
            return []
        results = []
        for f in sorted(p.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                results.append({"file": f.name, "data": json.loads(f.read_text())})
            except Exception:
                results.append({"file": f.name, "data": {}})
        return results
    except Exception:
        return []


def get_launchctl_agents():
    """Get Brotherhood agents from launchctl list."""
    known_prefixes = ("com.shelby", "com.atlas", "com.viper", "com.robotox",
                      "com.thor", "com.quant", "com.max", "com.soren",
                      "com.brotherhood", "com.garves", "com.oracle")
    try:
        result = subprocess.run(
            ["launchctl", "list"], capture_output=True, text=True, timeout=10
        )
        agents = []
        for line in result.stdout.splitlines()[1:]:  # skip header
            parts = line.split("\t")
            if len(parts) >= 3:
                label = parts[2]
                if any(label.startswith(p) for p in known_prefixes):
                    agents.append({
                        "pid": parts[0] if parts[0] != "-" else None,
                        "exit_code": parts[1],
                        "label": label,
                        "running": parts[0] != "-",
                    })
        return agents
    except Exception:
        return []


def get_system_metrics():
    """Get CPU/memory/disk without psutil."""
    metrics = {}
    try:
        # Uptime
        r = subprocess.run(["uptime"], capture_output=True, text=True, timeout=5)
        metrics["uptime"] = r.stdout.strip()
    except Exception:
        metrics["uptime"] = "unknown"
    try:
        # Disk
        r = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
        lines = r.stdout.strip().splitlines()
        if len(lines) > 1:
            parts = lines[1].split()
            metrics["disk"] = {
                "total": parts[1] if len(parts) > 1 else "?",
                "used": parts[2] if len(parts) > 2 else "?",
                "available": parts[3] if len(parts) > 3 else "?",
                "percent": parts[4] if len(parts) > 4 else "?",
            }
    except Exception:
        metrics["disk"] = {}
    try:
        # Memory (macOS)
        r = subprocess.run(
            ["vm_stat"], capture_output=True, text=True, timeout=5
        )
        metrics["memory_raw"] = r.stdout.strip()[:500]
    except Exception:
        metrics["memory_raw"] = "unknown"
    return metrics
