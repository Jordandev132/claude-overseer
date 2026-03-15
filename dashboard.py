#!/usr/bin/env python3
"""Brotherhood Dashboard v1.0 — Full 4-Quadrant Layout.

Money | Agents | Content & Leads | System.
Dark mode. Mobile-friendly. Auto-refreshes every 60s.
Port 8878.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, render_template_string

import config

sys.path.insert(0, str(Path.home() / "shared"))
try:
    from finances import get_monthly_summary as _fin_summary, get_alerts as _fin_alerts, get_upcoming_renewals as _fin_renewals, _load as _fin_load
    _HAS_FINANCES = True
except ImportError:
    _HAS_FINANCES = False

app = Flask(__name__)
log = logging.getLogger("dashboard")

TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="60">
<title>Brotherhood HQ</title>
<style>
  :root {
    --bg: #0a0e14; --card: #12171f; --card-hover: #161d27;
    --border: #1e2733; --border-light: #2a3545;
    --text: #c9d1d9; --dim: #6e7681; --white: #f0f6fc;
    --green: #3fb950; --green-bg: rgba(63,185,80,0.1);
    --yellow: #d29922; --yellow-bg: rgba(210,153,34,0.1);
    --red: #f85149; --red-bg: rgba(248,81,73,0.1);
    --blue: #58a6ff; --blue-bg: rgba(88,166,255,0.08);
    --purple: #bc8cff; --purple-bg: rgba(188,140,255,0.1);
    --cyan: #39d2c0;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    font-size: 14px; line-height: 1.5; padding: 16px 20px;
    min-height: 100vh;
  }

  /* Header */
  .header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid var(--border);
  }
  .header h1 { font-size: 22px; color: var(--white); font-weight: 700; letter-spacing: -0.5px; }
  .header-right { display: flex; gap: 10px; align-items: center; }
  .badge {
    padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;
    display: inline-flex; align-items: center; gap: 4px;
  }
  .badge-ok { background: var(--green-bg); color: var(--green); border: 1px solid rgba(63,185,80,0.3); }
  .badge-warn { background: var(--yellow-bg); color: var(--yellow); border: 1px solid rgba(210,153,34,0.3); }
  .badge-err { background: var(--red-bg); color: var(--red); border: 1px solid rgba(248,81,73,0.3); }
  .pulse { width: 6px; height: 6px; border-radius: 50%; background: var(--green); animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }

  /* Grid */
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }

  /* Cards */
  .card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: 16px; transition: border-color 0.2s;
  }
  .card:hover { border-color: var(--border-light); }
  .card-full { grid-column: 1 / -1; }
  .card-title {
    font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1.5px; margin-bottom: 12px; display: flex;
    align-items: center; gap: 8px;
  }
  .card-title .icon { font-size: 14px; }
  .ct-money { color: var(--green); }
  .ct-agents { color: var(--blue); }
  .ct-content { color: var(--purple); }
  .ct-system { color: var(--cyan); }

  /* Stats */
  .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .stat-box {
    background: rgba(255,255,255,0.02); border: 1px solid var(--border);
    border-radius: 8px; padding: 10px 12px;
  }
  .stat-label { font-size: 11px; color: var(--dim); text-transform: uppercase; letter-spacing: 0.5px; }
  .stat-val { font-size: 20px; font-weight: 700; margin-top: 2px; }
  .stat-sub { font-size: 11px; color: var(--dim); }

  /* Rows */
  .row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid var(--border); }
  .row:last-child { border-bottom: none; }
  .row-label { color: var(--dim); font-size: 13px; }
  .row-val { font-weight: 600; font-size: 13px; }

  /* Agent list */
  .agent-row {
    display: flex; align-items: center; gap: 10px; padding: 6px 0;
    border-bottom: 1px solid var(--border);
  }
  .agent-row:last-child { border-bottom: none; }
  .dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .dot-on { background: var(--green); box-shadow: 0 0 6px rgba(63,185,80,0.4); }
  .dot-off { background: var(--red); } .dot-paused { background: var(--yellow); }
  .dot-unknown { background: var(--dim); }
  .agent-name { flex: 1; font-weight: 500; font-size: 13px; }
  .agent-detail { color: var(--dim); font-size: 11px; max-width: 200px; text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  /* Lead card */
  .lead-item {
    background: rgba(255,255,255,0.02); border: 1px solid var(--border);
    border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;
  }
  .lead-item:last-child { margin-bottom: 0; }
  .lead-title { font-weight: 600; font-size: 13px; color: var(--white); }
  .lead-meta { font-size: 11px; color: var(--dim); margin-top: 2px; }
  .lead-score {
    display: inline-block; padding: 1px 6px; border-radius: 4px;
    font-size: 11px; font-weight: 700;
  }
  .score-hot { background: var(--green-bg); color: var(--green); }
  .score-warm { background: var(--yellow-bg); color: var(--yellow); }
  .score-cold { background: var(--blue-bg); color: var(--blue); }

  /* Content queue */
  .content-item {
    display: flex; align-items: center; gap: 8px; padding: 5px 0;
    border-bottom: 1px solid var(--border); font-size: 13px;
  }
  .content-item:last-child { border-bottom: none; }
  .platform-tag {
    font-size: 10px; font-weight: 700; padding: 1px 6px;
    border-radius: 4px; text-transform: uppercase; letter-spacing: 0.5px;
  }
  .tag-linkedin { background: rgba(0,119,181,0.2); color: #0a66c2; }
  .tag-x { background: rgba(255,255,255,0.08); color: var(--text); }
  .tag-tiktok { background: rgba(255,0,80,0.15); color: #ff0050; }
  .tag-instagram { background: rgba(225,48,108,0.15); color: #e1306c; }
  .tag-youtube { background: rgba(255,0,0,0.15); color: #ff0000; }

  /* Services */
  .svc-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid var(--border); }
  .svc-row:last-child { border-bottom: none; }
  .svc-name { font-weight: 500; font-size: 13px; }
  .svc-price { color: var(--green); font-size: 13px; font-weight: 600; }

  /* Claude brain */
  .reasoning {
    background: rgba(255,255,255,0.03); border: 1px solid var(--border);
    border-radius: 8px; padding: 12px; font-size: 13px; line-height: 1.6;
    color: var(--text);
  }
  .action-list { list-style: none; }
  .action-list li { padding: 3px 0; font-size: 13px; color: var(--dim); }
  .action-list li::before { content: "-> "; color: var(--blue); font-weight: 600; }
  .question {
    background: var(--yellow-bg); border: 1px solid rgba(210,153,34,0.3);
    border-radius: 6px; padding: 8px 12px; margin: 4px 0; font-size: 13px;
  }
  .directive {
    background: var(--purple-bg); border: 1px solid rgba(188,140,255,0.3);
    border-radius: 6px; padding: 8px 12px; margin: 4px 0; font-size: 13px;
  }

  /* Section headers */
  .section-header {
    font-size: 16px; font-weight: 700; color: var(--white);
    margin: 24px 0 12px 0; padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 8px;
  }
  .section-header:first-of-type { margin-top: 16px; }

  .empty { color: var(--dim); font-size: 13px; font-style: italic; padding: 8px 0; }

  /* Footer */
  .footer { color: var(--dim); font-size: 11px; text-align: center; margin-top: 20px; padding-top: 12px; border-top: 1px solid var(--border); }

  /* Mini-table */
  .mini-table { width: 100%; }
  .mini-table td { padding: 4px 0; font-size: 13px; border-bottom: 1px solid var(--border); }
  .mini-table tr:last-child td { border-bottom: none; }
  .mini-table td:last-child { text-align: right; font-weight: 600; }

  /* Thor list */
  .thor-item { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
  .thor-item:last-child { border-bottom: none; }
  .thor-task { flex: 1; color: var(--text); }
  .thor-badge { font-size: 10px; padding: 1px 6px; border-radius: 4px; font-weight: 600; }
  .tb-progress { background: var(--blue-bg); color: var(--blue); }
  .tb-pending { background: rgba(255,255,255,0.05); color: var(--dim); }

  /* Finance */
  .ct-finance { color: var(--yellow); }
  .fin-sub-row { display: flex; justify-content: space-between; align-items: center; padding: 5px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
  .fin-sub-row:last-child { border-bottom: none; }
  .proj-tag { font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 4px; }
  .proj-soren { background: rgba(232,121,249,0.15); color: #E879F9; }
  .proj-brotherhood { background: var(--blue-bg); color: var(--blue); }
  .proj-agency { background: var(--green-bg); color: var(--green); }
  .proj-other { background: rgba(255,255,255,0.05); color: var(--dim); }
  .green { color: var(--green); }
  .red { color: var(--red); }
  .yellow { color: var(--yellow); }
  .dim { color: var(--dim); }
</style>
</head>
<body>

<!-- HEADER -->
<div class="header">
  <h1>Brotherhood HQ</h1>
  <div class="header-right">
    <span class="badge {{ 'badge-ok' if health.active_issues == 0 else 'badge-warn' if health.active_issues < 5 else 'badge-err' }}">
      <span class="pulse"></span>
      {{ health.agents_online }}/{{ health.total_agents }} agents
    </span>
    <span class="badge {{ 'badge-ok' if costs.net_profit >= 0 else 'badge-err' }}">
      ${{ "%.0f"|format(costs.net_profit) }} net
    </span>
  </div>
</div>

<!-- Q1: MONEY -->
<div class="section-header"><span>$</span> Money</div>
<div class="grid">
  <div class="card">
    <div class="card-title ct-money"><span class="icon">$</span> P&L — {{ costs.month }}</div>
    <div class="stat-grid">
      <div class="stat-box">
        <div class="stat-label">Revenue</div>
        <div class="stat-val green">${{ "%.2f"|format(costs.total_revenue) }}</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Costs</div>
        <div class="stat-val red">${{ "%.2f"|format(costs.total_costs) }}</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Net Profit</div>
        <div class="stat-val {{ 'green' if costs.net_profit >= 0 else 'red' }}">${{ "%.2f"|format(costs.net_profit) }}</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Margin</div>
        <div class="stat-val {{ 'green' if costs.margin_percent > 0 else 'dim' }}">{{ "%.0f"|format(costs.margin_percent) }}%</div>
      </div>
    </div>
    {% if costs.breakdown %}
    <div style="margin-top: 12px;">
      <table class="mini-table">
        {% for name, info in costs.breakdown.items() %}
        <tr><td class="row-label">{{ name }}</td><td class="{{ 'red' if info.amount > 0 else 'dim' }}">${{ "%.2f"|format(info.amount) }}</td></tr>
        {% endfor %}
      </table>
    </div>
    {% endif %}
  </div>

  <div class="card">
    <div class="card-title ct-money"><span class="icon">*</span> Services</div>
    {% for svc in services %}
    <div class="svc-row">
      <span class="svc-name">{{ svc.name }}</span>
      <span class="svc-price">${{ svc.basic_price }}</span>
    </div>
    {% endfor %}
    {% if not services %}
    <div class="empty">No services configured.</div>
    {% endif %}
    <div style="margin-top: 10px;">
      <div class="row">
        <span class="row-label">Clients</span>
        <span class="row-val">{{ client_metrics.total_clients }}</span>
      </div>
      <div class="row">
        <span class="row-label">Active Retainers</span>
        <span class="row-val">{{ client_metrics.active_retainers }}</span>
      </div>
      <div class="row">
        <span class="row-label">Retainer MRR</span>
        <span class="row-val green">${{ "%.0f"|format(client_metrics.retainer_mrr) }}</span>
      </div>
    </div>
  </div>
</div>

<!-- PROFILES -->
<div class="grid" style="margin-top: 16px;">
  <div class="card card-full">
    <div class="card-title ct-money"><span class="icon">@</span> Agency Profiles</div>
    <div style="display: flex; gap: 12px; flex-wrap: wrap;">
      {% for name, prof in profiles.items() %}
      <div style="flex: 1; min-width: 200px; background: rgba(255,255,255,0.02); border: 1px solid var(--border); border-radius: 8px; padding: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <span style="font-weight: 600; font-size: 14px; color: var(--white);">{{ name|title }}</span>
          <span class="badge {{ 'badge-ok' if prof.status == 'live' else 'badge-warn' if prof.status == 'draft' else 'badge-err' }}">{{ prof.status }}</span>
        </div>
        {% if prof.username %}<div style="font-size: 12px; color: var(--dim);">@{{ prof.username }}</div>{% endif %}
        {% if prof.headline %}<div style="font-size: 12px; color: var(--text); margin-top: 4px;">{{ prof.headline[:60] }}</div>{% endif %}
        {% if prof.gigs %}<div style="font-size: 11px; color: var(--dim); margin-top: 4px;">{{ prof.gigs|length }} gig(s)</div>{% endif %}
        {% if prof.note %}<div style="font-size: 11px; color: var(--yellow); margin-top: 4px;">{{ prof.note }}</div>{% endif %}
      </div>
      {% endfor %}
    </div>
  </div>
</div>

<!-- FINANCES -->
<div class="section-header"><span>$</span> Finances</div>
<div class="grid">
  <div class="card">
    <div class="card-title ct-finance"><span class="icon">$</span> Monthly Summary — {{ fin.month }}</div>
    <div class="stat-grid">
      <div class="stat-box">
        <div class="stat-label">Total Costs</div>
        <div class="stat-val red">${{ "%.2f"|format(fin.total_costs) }}</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Revenue</div>
        <div class="stat-val green">${{ "%.2f"|format(fin.total_revenue) }}</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Net</div>
        <div class="stat-val {{ 'green' if fin.net >= 0 else 'red' }}">${{ "%.2f"|format(fin.net) }}</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Active Subs</div>
        <div class="stat-val">{{ fin.active_count }}</div>
      </div>
    </div>
    <div style="margin-top: 10px;">
      <div class="row">
        <span class="row-label">Subscriptions/mo</span>
        <span class="row-val red">${{ "%.2f"|format(fin.total_subscriptions) }}</span>
      </div>
      <div class="row">
        <span class="row-label">API Costs MTD</span>
        <span class="row-val red">${{ "%.2f"|format(fin.total_api) }}</span>
      </div>
      <div class="row">
        <span class="row-label">One-Time MTD</span>
        <span class="row-val red">${{ "%.2f"|format(fin.total_one_time) }}</span>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-title ct-finance"><span class="icon">*</span> Subscriptions</div>
    {% for sub in fin_subs %}
    <div class="fin-sub-row">
      <span style="flex:1;">{{ sub.name }}</span>
      <span class="proj-tag proj-{{ sub.project }}">{{ sub.project }}</span>
      <span style="width:70px; text-align:right; font-weight:600; font-family:monospace;">{{ "$%.2f"|format(sub.cost) if sub.cost > 0 else "FREE" }}</span>
    </div>
    {% endfor %}
    {% if not fin_subs %}
    <div class="empty">No subscriptions.</div>
    {% endif %}
  </div>
</div>

{% if fin.by_project %}
<div class="grid" style="margin-top: 12px;">
  <div class="card card-full">
    <div class="card-title ct-finance"><span class="icon">#</span> By Project</div>
    <div style="display: flex; gap: 12px; flex-wrap: wrap;">
      {% for proj, vals in fin.by_project.items() %}
      <div style="flex: 1; min-width: 160px; background: rgba(255,255,255,0.02); border: 1px solid var(--border); border-radius: 8px; padding: 12px;">
        <div style="font-weight: 700; font-size: 13px; color: var(--white); margin-bottom: 6px; text-transform: uppercase;">{{ proj }}</div>
        <div style="font-size: 12px;">Costs: <span class="red">${{ "%.2f"|format(vals.costs) }}</span></div>
        <div style="font-size: 12px;">Revenue: <span class="green">${{ "%.2f"|format(vals.revenue) }}</span></div>
        <div style="font-size: 12px;">Net: <span class="{{ 'green' if vals.net >= 0 else 'red' }}" style="font-weight:700;">${{ "%.2f"|format(vals.net) }}</span></div>
      </div>
      {% endfor %}
    </div>
  </div>
</div>
{% endif %}

{% if fin_alerts %}
<div class="grid" style="margin-top: 12px;">
  <div class="card card-full">
    <div class="card-title" style="color: var(--yellow);"><span class="icon">!</span> Financial Alerts</div>
    {% for a in fin_alerts %}
    <div class="question">{{ a }}</div>
    {% endfor %}
  </div>
</div>
{% endif %}

<!-- Q2: AGENTS -->
<div class="section-header"><span>@</span> Agents</div>
<div class="grid">
  <div class="card">
    <div class="card-title ct-agents"><span class="icon">@</span> Status</div>
    {% for name, info in agents.items() %}
    <div class="agent-row">
      <div class="dot {{ 'dot-on' if info.status in ('active','healthy','running') else 'dot-paused' if info.status == 'paused' else 'dot-off' if info.status in ('down','stopped','killed') else 'dot-unknown' }}"></div>
      <span class="agent-name">{{ name }}</span>
      <span class="agent-detail">{{ info.reason[:45] if info.reason else info.status }}</span>
    </div>
    {% endfor %}
    {% if not agents %}
    <div class="empty">No agent data available.</div>
    {% endif %}
  </div>

  <div class="card">
    <div class="card-title ct-system"><span class="icon">#</span> System Health</div>
    <div class="stat-grid">
      <div class="stat-box">
        <div class="stat-label">Status</div>
        <div class="stat-val {{ 'green' if health.overall_status == 'healthy' else 'yellow' }}">{{ health.overall_status }}</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Issues</div>
        <div class="stat-val {{ 'green' if health.active_issues == 0 else 'yellow' if health.active_issues < 5 else 'red' }}">{{ health.active_issues }}</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Disk Free</div>
        <div class="stat-val">{{ "%.0f"|format(health.disk_free_gb) }} GB</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Last Scan</div>
        <div class="stat-val" style="font-size: 13px;">{{ (health.last_check or "?")[:16] }}</div>
      </div>
    </div>
    {% if health.recent_alerts %}
    <div style="margin-top: 10px;">
      {% for a in health.recent_alerts[:4] %}
      <div class="question" style="background: var(--red-bg); border-color: rgba(248,81,73,0.3);">{{ a }}</div>
      {% endfor %}
    </div>
    {% endif %}
  </div>
</div>

<!-- Q3: CONTENT & LEADS -->
<div class="section-header"><span>></span> Content & Leads</div>
<div class="grid">
  <div class="card">
    <div class="card-title ct-purple"><span class="icon">></span> Max — Content Queue</div>
    {% if max_status %}
    <div class="stat-grid" style="margin-bottom: 10px;">
      <div class="stat-box">
        <div class="stat-label">Queued</div>
        <div class="stat-val purple">{{ max_status.queued|default(0) }}</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Posted</div>
        <div class="stat-val green">{{ max_status.posted|default(0) }}</div>
      </div>
    </div>
    {% endif %}
    {% for item in max_queue[:6] %}
    <div class="content-item">
      <span class="platform-tag tag-{{ item.platform|lower }}">{{ item.platform[:3] }}</span>
      <span style="flex:1; color: var(--text);">{{ item.title[:50] }}</span>
      <span class="row-label">{{ item.status|default('queued') }}</span>
    </div>
    {% endfor %}
    {% if not max_queue %}
    <div class="empty">No content in queue. Max will generate next cycle.</div>
    {% endif %}
  </div>

  <div class="card">
    <div class="card-title ct-money"><span class="icon">!</span> Viper — Top Leads</div>
    {% for lead in leads[:5] %}
    <div class="lead-item">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span class="lead-title">{{ lead.title[:45] }}</span>
        <span class="lead-score {{ 'score-hot' if lead.score >= 7.5 else 'score-warm' if lead.score >= 6.0 else 'score-cold' }}">{{ "%.1f"|format(lead.score) }}</span>
      </div>
      <div class="lead-meta">
        {{ lead.source|default('') }} {% if lead.budget %} | ${{ lead.budget }}{% endif %} {% if lead.service %} | {{ lead.service }}{% endif %}
      </div>
    </div>
    {% endfor %}
    {% if not leads %}
    <div class="empty">No leads yet. Viper is scanning.</div>
    {% endif %}
  </div>
</div>

<!-- Q4: CLAUDE BRAIN + THOR -->
<div class="section-header"><span>~</span> Intelligence</div>
<div class="grid">
  <div class="card card-full">
    <div class="card-title ct-system"><span class="icon">~</span> Claude — Last Cycle</div>
    {% if claude.last_cycle %}
    <div class="row" style="margin-bottom: 8px;">
      <span class="row-label">Ran at</span>
      <span class="row-val">{{ claude.last_cycle[:19] }}</span>
    </div>
    <div class="reasoning">{{ claude.reasoning }}</div>

    {% if claude.agent_actions %}
    <div style="margin-top: 12px;">
      <div class="card-title ct-agents" style="font-size: 10px;">Decisions</div>
      <ul class="action-list">
        {% for agent, action in claude.agent_actions.items() %}
        <li><strong>{{ agent }}</strong> {{ action }}</li>
        {% endfor %}
      </ul>
    </div>
    {% endif %}

    {% if claude.questions_for_jordan %}
    <div style="margin-top: 12px;">
      <div class="card-title" style="font-size: 10px; color: var(--yellow);">Questions for Jordan</div>
      {% for q in claude.questions_for_jordan %}
      <div class="question">{{ q }}</div>
      {% endfor %}
    </div>
    {% endif %}

    {% if claude.content_directives %}
    <div style="margin-top: 12px;">
      <div class="card-title" style="font-size: 10px; color: var(--purple);">Content Directives</div>
      {% for cd in claude.content_directives %}
      <div class="directive"><strong>{{ cd.agent }}</strong> -> {{ cd.platform }}: {{ cd.topic }}</div>
      {% endfor %}
    </div>
    {% endif %}

    <div style="margin-top: 8px; color: var(--dim); font-size: 11px;">
      Actions: {{ claude.actions_taken|length }} | Tasks: {{ claude.task_count }} | Alerts: {{ claude.alert_count }}
    </div>
    {% else %}
    <div class="empty">Overseer hasn't run yet.</div>
    {% endif %}
  </div>

  <div class="card">
    <div class="card-title ct-system"><span class="icon">></span> Thor Queue</div>
    {% for t in thor_tasks[:8] %}
    <div class="thor-item">
      <span class="thor-task">{{ t.task[:50] }}</span>
      <span class="thor-badge {{ 'tb-progress' if t.status == 'in_progress' else 'tb-pending' }}">P{{ t.priority }} {{ t.status }}</span>
    </div>
    {% endfor %}
    {% if not thor_tasks %}
    <div class="empty">No tasks in queue.</div>
    {% endif %}
  </div>

  <div class="card">
    <div class="card-title ct-agents"><span class="icon">|</span> Pipeline</div>
    {% if pipeline %}
    {% for stage, count in pipeline.items() %}
    <div class="row">
      <span class="row-label">{{ stage|replace('_', ' ')|title }}</span>
      <span class="row-val">{{ count }}</span>
    </div>
    {% endfor %}
    {% else %}
    <div class="row">
      <span class="row-label">Active Leads</span>
      <span class="row-val">{{ leads|length }}</span>
    </div>
    <div class="row">
      <span class="row-label">Proposals Sent</span>
      <span class="row-val">{{ client_metrics.proposals_sent|default(0) }}</span>
    </div>
    <div class="row">
      <span class="row-label">Won</span>
      <span class="row-val green">{{ client_metrics.total_clients }}</span>
    </div>
    {% endif %}
  </div>
</div>

<div class="footer">
  Brotherhood HQ v1.0 — Auto-refreshes 60s — Darkcode AI
</div>
</body>
</html>
"""


_FIN_DEFAULTS = {"month": "2026-03", "total_costs": 0, "total_revenue": 0,
                  "net": 0, "total_subscriptions": 0, "total_api": 0,
                  "total_one_time": 0, "active_count": 0, "by_project": {}}


def _load_finances():
    """Load finance data. Returns (summary, subscriptions, alerts)."""
    if not _HAS_FINANCES:
        return _FIN_DEFAULTS.copy(), [], []
    try:
        summary = _fin_summary()
        data = _fin_load()
        subs = [s for s in data.get("subscriptions", []) if s.get("status") == "active"]
        summary["active_count"] = len(subs)
        for p in ("agency", "max"):
            if p not in summary.get("by_project", {}):
                summary.setdefault("by_project", {})[p] = {"costs": 0, "revenue": 0, "net": 0}
        return summary, subs, _fin_alerts()
    except Exception:
        return _FIN_DEFAULTS.copy(), [], []


def _load(path: Path, default=None):
    if not path.exists():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return default if default is not None else {}


@app.route("/")
def index():
    # -- Claude status --
    claude = _load(config.STATUS_FILE, {})

    # -- Costs --
    costs_raw = _load(config.COSTS_FILE, {})
    costs_obj = type("C", (), {
        "total_revenue": costs_raw.get("total_revenue", 0),
        "total_costs": costs_raw.get("total_costs", 0),
        "net_profit": costs_raw.get("net_profit", 0),
        "margin_percent": costs_raw.get("margin_percent", 0),
        "month": costs_raw.get("month", "2026-03"),
        "breakdown": costs_raw.get("costs", {}),
    })()

    # -- Health --
    health_raw = _load(config.HEALTH_STATUS_FILE, {})
    sys_info = health_raw.get("system", {})
    health_obj = type("H", (), {
        "overall_status": health_raw.get("overall_status", "unknown"),
        "agents_online": health_raw.get("agents_online", 0),
        "total_agents": health_raw.get("total_agents", 0),
        "active_issues": health_raw.get("active_issues", 0),
        "last_check": health_raw.get("last_check", ""),
        "disk_free_gb": sys_info.get("disk_free_gb", 0),
        "recent_alerts": health_raw.get("recent_alerts", []),
    })()

    # -- Agents from memory + health --
    memory = _load(config.MEMORY_FILE, {})
    agents = {}
    for name, state in memory.get("agent_state_history", {}).items():
        agents[name] = {
            "status": state.get("status", "unknown"),
            "reason": state.get("reason", ""),
        }
    # Merge Robotox agent details if available
    for name, detail in health_raw.get("agents", {}).items():
        if name == "summary":
            continue
        if name not in agents:
            agents[name] = {
                "status": detail.get("status", "unknown") if isinstance(detail, dict) else "unknown",
                "reason": "",
            }

    # -- Services --
    svc_raw = _load(config.SERVICES_FILE, {})
    services = []
    for s in svc_raw.get("services", []):
        tiers = s.get("tiers", {})
        basic = tiers.get("basic", {})
        price = basic.get("price_setup", basic.get("price_flat", 0))
        services.append({
            "name": s.get("name", ""),
            "basic_price": price,
        })

    # -- Clients --
    clients_raw = _load(config.CLIENTS_FILE, {})
    client_metrics = clients_raw.get("metrics", {
        "total_clients": 0,
        "active_retainers": 0,
        "retainer_mrr": 0,
    })
    pipeline_raw = clients_raw.get("pipeline", {}).get("current", {})
    pipeline = {}
    stages = clients_raw.get("pipeline", {}).get("stages", [])
    for stage in stages:
        count = len(pipeline_raw.get(stage, [])) if isinstance(pipeline_raw.get(stage), list) else pipeline_raw.get(stage, 0)
        if count:
            pipeline[stage] = count

    # -- Profiles --
    profiles_raw = _load(config.PROFILES_FILE, {})
    profiles = {}
    for name, prof in profiles_raw.get("platforms", {}).items():
        profiles[name] = {
            "status": prof.get("status", "unknown"),
            "username": prof.get("username", ""),
            "headline": prof.get("headline", ""),
            "gigs": prof.get("gigs", []),
            "note": prof.get("note", ""),
        }

    # -- Max content queue --
    max_status_raw = _load(config.MAX_STATUS_FILE, {})
    max_queue_raw = _load(config.MAX_QUEUE_FILE, {})
    max_queue = []
    items = max_queue_raw.get("queue", max_queue_raw) if isinstance(max_queue_raw, dict) else max_queue_raw
    if isinstance(items, list):
        for item in items:
            max_queue.append({
                "platform": item.get("platform", "unknown"),
                "title": item.get("title", item.get("hook", item.get("content", "")[:50])),
                "status": item.get("status", "queued"),
            })
    max_status = {
        "queued": sum(1 for i in max_queue if i.get("status") == "queued"),
        "posted": sum(1 for i in max_queue if i.get("status") == "posted"),
    }

    # -- Viper leads --
    leads_raw = _load(config.VIPER_LEADS_FILE, {})
    leads_list = leads_raw.get("leads", leads_raw) if isinstance(leads_raw, dict) else leads_raw
    leads = []
    if isinstance(leads_list, list):
        for l in leads_list:
            leads.append({
                "title": l.get("title", l.get("name", "")),
                "score": l.get("composite_score", l.get("score", 0)),
                "source": l.get("source", ""),
                "budget": l.get("budget", l.get("budget_usd", "")),
                "service": l.get("matched_service", l.get("service", "")),
            })
        leads.sort(key=lambda x: x["score"], reverse=True)

    # -- Thor tasks --
    thor_raw = _load(config.THOR_QUEUE_FILE, {})
    thor_tasks = thor_raw.get("tasks", [])
    for t in thor_tasks:
        t.setdefault("priority", 1)
        t.setdefault("status", "pending")

    # -- Finances --
    fin_summary, fin_subs, fin_alerts = _load_finances()

    return render_template_string(
        TEMPLATE,
        claude=claude,
        costs=costs_obj,
        health=health_obj,
        agents=agents,
        services=services,
        client_metrics=client_metrics,
        pipeline=pipeline,
        max_status=max_status,
        max_queue=max_queue,
        leads=leads,
        thor_tasks=thor_tasks,
        profiles=profiles,
        fin=fin_summary,
        fin_subs=fin_subs,
        fin_alerts=fin_alerts,
    )


@app.route("/api/status")
def api_status():
    """JSON API for other agents."""
    return {
        "claude": _load(config.STATUS_FILE),
        "health": _load(config.HEALTH_STATUS_FILE),
        "costs": _load(config.COSTS_FILE),
        "memory": _load(config.MEMORY_FILE),
        "services": _load(config.SERVICES_FILE),
        "clients": _load(config.CLIENTS_FILE),
        "leads": _load(config.VIPER_LEADS_FILE),
        "max_status": _load(config.MAX_STATUS_FILE),
    }


@app.route("/api/finances")
def api_finances():
    """Finances JSON API."""
    if not _HAS_FINANCES:
        return {"error": "finances module not available"}, 500
    try:
        data = _fin_load()
        return {
            "subscriptions": data.get("subscriptions", []),
            "api_costs": data.get("api_costs", []),
            "one_time_costs": data.get("one_time_costs", []),
            "revenue": data.get("revenue", []),
            "summary": _fin_summary(),
            "alerts": _fin_alerts(),
            "upcoming_renewals": _fin_renewals(),
        }
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8878, debug=False)
