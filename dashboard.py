#!/usr/bin/env python3
"""Brotherhood Dashboard v1.0 — Full 4-Quadrant Layout.

Money | Agents | Content & Leads | System.
Dark mode. Mobile-friendly. Auto-refreshes every 60s.
Port 8878.
"""

import json
import logging
from pathlib import Path

import os
import sys
sys.path.insert(0, str(Path.home()))  # sentinel package
from flask import jsonify, Flask, render_template_string, request

try:
    import config
except Exception:
    config = None  # Render deployment — API-only mode

app = Flask(__name__)

from brotherhood_api import bp as brotherhood_bp  # noqa: E402
app.register_blueprint(brotherhood_bp)
log = logging.getLogger("dashboard")

TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Brotherhood HQ</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='%230c0c14'/><rect x='12' y='12' width='32' height='32' rx='6' fill='%234a9eff'/><rect x='56' y='12' width='32' height='32' rx='6' fill='%23a78bfa'/><rect x='12' y='56' width='32' height='32' rx='6' fill='%2334d399'/><rect x='56' y='56' width='32' height='32' rx='6' fill='%23C9A84C'/></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700;800&family=Nunito+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:#050507;--card:#0c0c14;--card-hover:#111119;
    --border:rgba(255,255,255,.06);--border-hover:rgba(255,255,255,.12);--border-solid:#1e1e2e;
    --text:#e2e2e8;--muted:#9ca3af;--dim:#6b7280;--white:#f8f8fc;
    --green:#34d399;--green-bg:rgba(52,211,153,.08);
    --yellow:#eab308;--yellow-bg:rgba(234,179,8,.08);
    --red:#f87171;--red-bg:rgba(248,113,113,.08);
    --blue:#4a9eff;--blue-bg:rgba(74,158,255,.08);
    --purple:#a78bfa;--purple-bg:rgba(167,139,250,.08);
    --cyan:#22d3ee;--gold:#C9A84C;--gold-glow:rgba(201,168,76,.15);
    --radius:16px;--radius-sm:10px;--radius-xs:8px;
    --font-head:'Rubik',system-ui,sans-serif;
    --font-body:'Nunito Sans',system-ui,sans-serif;
  }
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:var(--bg);color:var(--text);font-family:var(--font-body);font-size:14px;line-height:1.5;min-height:100vh;-webkit-font-smoothing:antialiased}
  .container{max-width:1200px;margin:0 auto;padding:16px 20px}
  ::-webkit-scrollbar{width:5px}
  ::-webkit-scrollbar-track{background:transparent}
  ::-webkit-scrollbar-thumb{background:var(--border-solid);border-radius:3px}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
  @media(prefers-reduced-motion:reduce){*{animation-duration:0s!important;transition-duration:0s!important}}

  /* Header */
  header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;padding-bottom:12px;border-bottom:1px solid var(--border)}
  header h1{font-family:var(--font-head);font-size:22px;color:var(--white);font-weight:700;letter-spacing:-.5px}
  .header-right{display:flex;gap:10px;align-items:center}
  .badge{padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;display:inline-flex;align-items:center;gap:4px}
  .badge-ok{background:var(--green-bg);color:var(--green);border:1px solid rgba(52,211,153,.2)}
  .badge-warn{background:var(--yellow-bg);color:var(--yellow);border:1px solid rgba(234,179,8,.2)}
  .badge-err{background:var(--red-bg);color:var(--red);border:1px solid rgba(248,113,113,.2)}
  .pulse{width:6px;height:6px;border-radius:50%;background:var(--green);animation:pulse 2s infinite}

  /* Grid */
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
  @media(max-width:900px){.grid{grid-template-columns:1fr}}

  /* Cards */
  .card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius-sm);padding:16px;transition:border-color .2s;position:relative;overflow:hidden}
  .card::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.04),transparent)}
  .card:hover{border-color:var(--border-hover)}
  .card-full{grid-column:1/-1}
  .card-title{font-family:var(--font-head);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;display:flex;align-items:center;gap:8px}
  .ct-money{color:var(--green)}.ct-agents{color:var(--blue)}.ct-content{color:var(--purple)}.ct-system{color:var(--cyan)}.ct-finance{color:var(--yellow)}

  /* Stats */
  .stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
  .stat-box{background:rgba(255,255,255,.02);border:1px solid var(--border);border-radius:var(--radius-xs);padding:10px 12px}
  .stat-label{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
  .stat-val{font-family:var(--font-head);font-size:20px;font-weight:700;margin-top:2px;font-variant-numeric:tabular-nums}

  /* Rows */
  .row{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border)}
  .row:last-child{border-bottom:none}
  .row-label{color:var(--muted);font-size:13px}
  .row-val{font-family:var(--font-head);font-weight:600;font-size:13px}

  /* Agent list */
  .agent-row{display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid var(--border)}
  .agent-row:last-child{border-bottom:none}
  .dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
  .dot-on{background:var(--green);box-shadow:0 0 6px rgba(52,211,153,.4)}
  .dot-off{background:var(--red)}.dot-paused{background:var(--yellow)}.dot-unknown{background:var(--dim)}
  .agent-name{flex:1;font-weight:500;font-size:13px}
  .agent-detail{color:var(--muted);font-size:12px;max-width:200px;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

  /* Lead card */
  .lead-item{background:rgba(255,255,255,.02);border:1px solid var(--border);border-radius:var(--radius-xs);padding:10px 12px;margin-bottom:8px}
  .lead-item:last-child{margin-bottom:0}
  .lead-title{font-family:var(--font-head);font-weight:600;font-size:13px;color:var(--white)}
  .lead-meta{font-size:12px;color:var(--muted);margin-top:2px}
  .lead-score{display:inline-block;padding:1px 6px;border-radius:4px;font-family:var(--font-head);font-size:11px;font-weight:700}
  .score-hot{background:var(--green-bg);color:var(--green)}
  .score-warm{background:var(--yellow-bg);color:var(--yellow)}
  .score-cold{background:var(--blue-bg);color:var(--blue)}

  /* Content queue */
  .content-item{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid var(--border);font-size:13px}
  .content-item:last-child{border-bottom:none}
  .platform-tag{font-family:var(--font-head);font-size:10px;font-weight:700;padding:2px 8px;border-radius:4px;text-transform:uppercase;letter-spacing:.5px}
  .tag-linkedin{background:rgba(0,119,181,.15);color:#3b82f6}
  .tag-x{background:rgba(255,255,255,.06);color:var(--text)}
  .tag-tiktok{background:rgba(255,0,80,.1);color:#fb7185}
  .tag-instagram{background:rgba(225,48,108,.1);color:#f472b6}
  .tag-youtube{background:rgba(255,0,0,.1);color:#f87171}

  /* Services */
  .svc-row{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border)}
  .svc-row:last-child{border-bottom:none}
  .svc-name{font-weight:500;font-size:13px}
  .svc-price{color:var(--green);font-family:var(--font-head);font-size:13px;font-weight:600}

  /* Claude brain */
  .reasoning{background:rgba(255,255,255,.02);border:1px solid var(--border);border-radius:var(--radius-xs);padding:12px;font-size:13px;line-height:1.6;color:var(--text)}
  .action-list{list-style:none}
  .action-list li{padding:3px 0;font-size:13px;color:var(--muted)}
  .action-list li::before{content:"-> ";color:var(--blue);font-weight:600}
  .question{background:var(--yellow-bg);border:1px solid rgba(234,179,8,.2);border-radius:6px;padding:8px 12px;margin:4px 0;font-size:13px}
  .directive{background:var(--purple-bg);border:1px solid rgba(167,139,250,.2);border-radius:6px;padding:8px 12px;margin:4px 0;font-size:13px}

  /* Section headers */
  .section-header{font-family:var(--font-head);font-size:16px;font-weight:700;color:var(--white);margin:24px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px}
  .section-header:first-of-type{margin-top:16px}
  .empty{color:var(--muted);font-size:13px;font-style:italic;padding:8px 0}

  /* Footer */
  footer{color:var(--muted);font-size:12px;text-align:center;margin-top:20px;padding-top:12px;border-top:1px solid var(--border)}

  /* Mini-table */
  .mini-table{width:100%}
  .mini-table td{padding:4px 0;font-size:13px;border-bottom:1px solid var(--border)}
  .mini-table tr:last-child td{border-bottom:none}
  .mini-table td:last-child{text-align:right;font-family:var(--font-head);font-weight:600}

  /* Thor list */
  .thor-item{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--border);font-size:13px}
  .thor-item:last-child{border-bottom:none}
  .thor-task{flex:1;color:var(--text)}
  .thor-badge{font-family:var(--font-head);font-size:10px;padding:2px 8px;border-radius:4px;font-weight:600}
  .tb-progress{background:var(--blue-bg);color:var(--blue)}
  .tb-pending{background:rgba(255,255,255,.04);color:var(--dim)}

  /* Finance */
  .fin-sub-row{display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid var(--border);font-size:13px}
  .fin-sub-row:last-child{border-bottom:none}
  .proj-tag{font-family:var(--font-head);font-size:10px;font-weight:700;padding:2px 8px;border-radius:4px}
  .proj-soren{background:rgba(232,121,249,.1);color:#E879F9}
  .proj-brotherhood{background:var(--blue-bg);color:var(--blue)}
  .proj-agency{background:var(--green-bg);color:var(--green)}
  .proj-other{background:rgba(255,255,255,.04);color:var(--dim)}
  .proj-max{background:rgba(251,146,60,.08);color:#fb923c}
  .green{color:var(--green)}.red{color:var(--red)}.yellow{color:var(--yellow)}.dim{color:var(--dim)}

  /* Pipeline counters */
  .pipeline-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:16px}
  .pipeline-stat{background:var(--card);border:1px solid var(--border);border-radius:var(--radius-xs);padding:12px}
  .pipeline-stat .ps-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
  .pipeline-stat .ps-val{font-family:var(--font-head);font-size:24px;font-weight:800;margin-top:2px;font-variant-numeric:tabular-nums}

  /* Data table */
  .data-table{width:100%;border-collapse:collapse;font-size:12px}
  .data-table th{padding:8px;text-align:left;color:var(--muted);font-family:var(--font-head);font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--border)}
  .data-table td{padding:8px;border-bottom:1px solid var(--border);vertical-align:middle}
  .data-table tr:hover td{background:rgba(255,255,255,.02)}
  .data-table a{color:var(--blue);text-decoration:none;font-size:11px}
  .data-table a:hover{text-decoration:underline}
  .niche-badge{padding:2px 8px;border-radius:4px;font-family:var(--font-head);font-size:10px;font-weight:600;display:inline-block}

  @media(max-width:768px){.pipeline-grid{grid-template-columns:repeat(2,1fr)}}
  @media(max-width:480px){.pipeline-grid{grid-template-columns:1fr 1fr}}
</style>
</head>
<body>
<div class="container">

<!-- HEADER -->
<header>
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
</header>

<main>

<!-- Q1: MONEY -->
<div class="section-header">Money</div>
<div class="grid">
  <div class="card">
    <div class="card-title ct-money">P&L — {{ costs.month }}</div>
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
      <table class="mini-table" aria-label="Cost breakdown">
        {% for name, info in costs.breakdown.items() %}
        <tr><td class="row-label">{{ name }}</td><td class="{{ 'red' if info.amount > 0 else 'dim' }}">${{ "%.2f"|format(info.amount) }}</td></tr>
        {% endfor %}
      </table>
    </div>
    {% endif %}
  </div>

  <div class="card">
    <div class="card-title ct-money">Services</div>
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
    <div class="card-title ct-money">Agency Profiles</div>
    <div style="display: flex; gap: 12px; flex-wrap: wrap;">
      {% for name, prof in profiles.items() %}
      <div style="flex: 1; min-width: 200px; background: rgba(255,255,255,.02); border: 1px solid var(--border); border-radius: var(--radius-xs); padding: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <span style="font-family:var(--font-head);font-weight: 600; font-size: 14px; color: var(--white);">{{ name|title }}</span>
          <span class="badge {{ 'badge-ok' if prof.status == 'live' else 'badge-warn' if prof.status == 'draft' else 'badge-err' }}">{{ prof.status }}</span>
        </div>
        {% if prof.username %}<div style="font-size: 12px; color: var(--muted);">@{{ prof.username }}</div>{% endif %}
        {% if prof.headline %}<div style="font-size: 12px; color: var(--text); margin-top: 4px;">{{ prof.headline[:60] }}</div>{% endif %}
        {% if prof.gigs %}<div style="font-size: 12px; color: var(--muted); margin-top: 4px;">{{ prof.gigs|length }} gig(s)</div>{% endif %}
        {% if prof.note %}<div style="font-size: 12px; color: var(--yellow); margin-top: 4px;">{{ prof.note }}</div>{% endif %}
      </div>
      {% endfor %}
    </div>
  </div>
</div>

<!-- FINANCES -->
<div class="section-header">Finances</div>
<div class="grid">
  <div class="card">
    <div class="card-title ct-finance">Monthly Summary — {{ fin.month }}</div>
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
    <div class="card-title ct-finance">Subscriptions</div>
    {% for sub in fin_subs %}
    <div class="fin-sub-row">
      <span style="flex:1;">{{ sub.name }}</span>
      <span class="proj-tag proj-{{ sub.project }}">{{ sub.project }}</span>
      <span style="width:70px; text-align:right; font-family:var(--font-head); font-weight:600;">{{ "$%.2f"|format(sub.cost) if sub.cost > 0 else "FREE" }}</span>
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
    <div class="card-title ct-finance">By Project</div>
    <div style="display: flex; gap: 12px; flex-wrap: wrap;">
      {% for proj, vals in fin.by_project.items() %}
      <div style="flex: 1; min-width: 160px; background: rgba(255,255,255,.02); border: 1px solid var(--border); border-radius: var(--radius-xs); padding: 12px;">
        <div style="font-family:var(--font-head);font-weight: 700; font-size: 13px; color: var(--white); margin-bottom: 6px; text-transform: uppercase;">{{ proj }}</div>
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
    <div class="card-title" style="color: var(--yellow);">Financial Alerts</div>
    {% for a in fin_alerts %}
    <div class="question">{{ a }}</div>
    {% endfor %}
  </div>
</div>
{% endif %}

<!-- Q2: AGENTS -->
<div class="section-header">Agents</div>
<div class="grid">
  <div class="card">
    <div class="card-title ct-agents">Status</div>
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
    <div class="card-title ct-system">System Health</div>
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
      <div class="question" style="background: var(--red-bg); border-color: rgba(248,113,113,.2);">{{ a }}</div>
      {% endfor %}
    </div>
    {% endif %}
  </div>
</div>

<!-- Q3: CONTENT & LEADS -->
<div class="section-header">Content & Leads</div>
<div class="grid">
  <div class="card">
    <div class="card-title ct-content">Max — Content Queue</div>
    {% if max_status %}
    <div class="stat-grid" style="margin-bottom: 10px;">
      <div class="stat-box">
        <div class="stat-label">Queued</div>
        <div class="stat-val" style="color:var(--purple)">{{ max_status.queued|default(0) }}</div>
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
    <div class="card-title ct-money">Viper — Top Leads</div>
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

<!-- LEADS PIPELINE -->
<div class="section-header">Leads Pipeline</div>
<div class="pipeline-grid">
  <div class="pipeline-stat" style="border-left:3px solid var(--green);">
    <div class="ps-label">Total Pipeline</div>
    <div class="ps-val" style="color:var(--green);">{{ outreach.total }}</div>
  </div>
  <div class="pipeline-stat" style="border-left:3px solid var(--yellow);">
    <div class="ps-label">Gate 1 (BID)</div>
    <div class="ps-val" style="color:var(--yellow);">{{ outreach.approved }}</div>
  </div>
  <div class="pipeline-stat" style="border-left:3px solid var(--blue);">
    <div class="ps-label">Emails Sent</div>
    <div class="ps-val" style="color:var(--blue);">{{ outreach.sent }}</div>
  </div>
  <div class="pipeline-stat" style="border-left:3px solid var(--red);">
    <div class="ps-label">Declined</div>
    <div class="ps-val" style="color:var(--red);">{{ outreach.declined }}</div>
  </div>
  <div class="pipeline-stat" style="border-left:3px solid var(--purple);">
    <div class="ps-label">Sequences</div>
    <div class="ps-val" style="color:var(--purple);">{{ outreach.sequences }}</div>
    <div style="font-size:10px;color:var(--muted);margin-top:2px;">{{ outreach.seq_paused }} paused</div>
  </div>
</div>

<!-- Funnel + Niche -->
<div class="grid">
  <div class="card">
    <div class="card-title ct-agents">Pipeline Funnel</div>
    {% for stage, count in outreach.stages.items() %}
    <div style="display:flex;align-items:center;gap:8px;padding:4px 0;">
      <span style="width:100px;font-size:12px;color:var(--muted);text-transform:capitalize;">{{ stage.replace('_',' ') }}</span>
      <div style="flex:1;background:rgba(255,255,255,.04);border-radius:3px;height:8px;overflow:hidden;">
        <div style="height:100%;width:{{ (count / outreach.total * 100) if outreach.total > 0 else 0 }}%;background:{% if stage == 'sent' %}var(--blue){% elif stage == 'approved' %}var(--green){% elif stage == 'declined' %}var(--red){% else %}var(--dim){% endif %};border-radius:3px;"></div>
      </div>
      <span style="font-family:var(--font-head);font-size:12px;font-weight:700;width:32px;text-align:right;">{{ count }}</span>
    </div>
    {% endfor %}
  </div>

  <div class="card">
    <div class="card-title ct-content">By Niche</div>
    {% for niche, count in outreach.by_niche.items() %}
    <div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid var(--border);">
      <span style="font-size:12px;color:var(--text);">
        <span style="display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;background:{% if 'dental' in niche.lower() %}var(--blue){% elif 'real' in niche.lower() %}var(--green){% elif 'hvac' in niche.lower() %}var(--yellow){% elif 'legal' in niche.lower() or 'law' in niche.lower() %}var(--red){% elif 'med' in niche.lower() or 'spa' in niche.lower() %}#ec4899{% elif 'commercial' in niche.lower() %}var(--purple){% else %}var(--dim){% endif %};"></span>
        {{ niche }}
      </span>
      <span style="font-family:var(--font-head);font-size:12px;font-weight:700;">{{ count }}</span>
    </div>
    {% endfor %}
  </div>
</div>

<!-- Lead Table -->
<div class="grid" style="margin-top:12px;">
  <div class="card card-full">
    <div class="card-title ct-money">Active Leads ({{ outreach_table|length }})</div>
    <div style="overflow-x:auto;">
      <table class="data-table" aria-label="Active leads">
        <thead>
          <tr>
            <th scope="col">Business</th>
            <th scope="col">Niche</th>
            <th scope="col">Location</th>
            <th scope="col">Score</th>
            <th scope="col">Contact</th>
            <th scope="col">Stage</th>
            <th scope="col">Demo</th>
          </tr>
        </thead>
        <tbody>
          {% for l in outreach_table[:30] %}
          <tr>
            <td style="font-weight:500;color:var(--white);max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ l.name }}</td>
            <td>
              <span class="niche-badge" style="background:{% if 'dental' in l.niche.lower() %}var(--blue-bg);color:var(--blue){% elif 'real' in l.niche.lower() %}var(--green-bg);color:var(--green){% elif 'hvac' in l.niche.lower() %}var(--yellow-bg);color:var(--yellow){% elif 'legal' in l.niche.lower() or 'law' in l.niche.lower() %}var(--red-bg);color:var(--red){% elif 'commercial' in l.niche.lower() %}var(--purple-bg);color:var(--purple){% else %}rgba(255,255,255,.04);color:var(--dim){% endif %};">{{ l.niche }}</span>
            </td>
            <td style="color:var(--muted);font-size:12px;">{{ [l.city, l.state]|select|join(', ') }}</td>
            <td style="text-align:center;font-family:var(--font-head);font-weight:700;color:{{ 'var(--green)' if l.score >= 70 else 'var(--yellow)' if l.score >= 50 else 'var(--red)' }};">{{ l.score }}</td>
            <td style="color:var(--muted);font-size:12px;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ l.contact or '—' }}</td>
            <td style="text-align:center;">
              <span class="niche-badge" style="{{ 'background:var(--blue-bg);color:var(--blue);' if l.status == 'sent' else 'background:var(--green-bg);color:var(--green);' }}">{{ l.status }}</span>
            </td>
            <td style="text-align:center;">{% if l.demo_url %}<a href="{{ l.demo_url }}" target="_blank" rel="noopener" aria-label="View demo for {{ l.name }}">View</a>{% else %}—{% endif %}</td>
          </tr>
          {% endfor %}
          {% if outreach_table|length > 30 %}
          <tr><td colspan="7" style="padding:8px;text-align:center;color:var(--muted);font-size:12px;">Showing 30 of {{ outreach_table|length }} leads</td></tr>
          {% endif %}
        </tbody>
      </table>
    </div>
    {% if not outreach_table %}
    <div class="empty">No active leads. Viper is scanning.</div>
    {% endif %}
  </div>
</div>

<!-- Q4: INTELLIGENCE -->
<div class="section-header">Intelligence</div>
<div class="grid">
  <div class="card card-full">
    <div class="card-title ct-system">Claude — Last Cycle</div>
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

    <div style="margin-top: 8px; color: var(--muted); font-size: 12px;">
      Actions: {{ claude.actions_taken|length }} | Tasks: {{ claude.task_count }} | Alerts: {{ claude.alert_count }}
    </div>
    {% else %}
    <div class="empty">Overseer hasn't run yet.</div>
    {% endif %}
  </div>

  <div class="card">
    <div class="card-title ct-system">Thor Queue</div>
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
    <div class="card-title ct-agents">Pipeline</div>
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

</main>

<footer>
  Brotherhood HQ v2.0 — Auto-refreshes 10s — DarkCode AI
</footer>

</div>

<script>
// JS-based auto-refresh instead of meta refresh (preserves scroll position)
setTimeout(function(){location.reload()},10000);
</script>
</body>
</html>
"""



def _load(path, default=None):
    if path is None or not Path(path).exists():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return default if default is not None else {}


@app.route("/")
def index():
    if config is None:
        return jsonify({"status": "API-only mode", "endpoints": ["/api/grade", "/api/grade-subscribe", "/api/roi-subscribe"]}), 200
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

    # -- Health (LIVE from Robotox) --
    _robotox_status = _load(Path.home() / "sentinel" / "data" / "status.json", {})
    _robotox_health = _load(Path.home() / "sentinel" / "data" / "health_log.json", [])
    _robotox_self = _load(Path.home() / "sentinel" / "data" / "self_monitor.json", {})
    _latest_scan = _robotox_health[-1] if _robotox_health else {}
    _sys_info = _latest_scan.get("system", {})
    _agents_raw = _latest_scan.get("agents", {})
    _online_count = sum(1 for a in _agents_raw.values() if a is True or (isinstance(a, dict) and a.get("running")))
    _total_count = len(_agents_raw)

    # Get disk free via shutil (live, not cached)
    import shutil
    try:
        _disk = shutil.disk_usage("/")
        _disk_free_gb = round(_disk.free / (1024**3), 1)
    except Exception:
        _disk_free_gb = _sys_info.get("disk_free_gb", 0)

    health_obj = type("H", (), {
        "overall_status": "healthy" if _online_count >= 5 else ("warning" if _online_count >= 3 else "critical"),
        "agents_online": _online_count,
        "total_agents": _total_count,
        "active_issues": _latest_scan.get("issues", 0) if isinstance(_latest_scan.get("issues"), int) else len(_latest_scan.get("issues", [])),
        "last_check": _robotox_status.get("last_scan", _latest_scan.get("timestamp", "")),
        "disk_free_gb": _disk_free_gb,
        "recent_alerts": [],
    })()

    # -- Agents (LIVE from Robotox + launchctl config) --
    from sentinel.config import AGENTS as _SENTINEL_AGENTS
    agents = {}
    for name, cfg in _SENTINEL_AGENTS.items():
        if cfg.get("disabled"):
            agents[name] = {"status": "killed" if name in ("hawk", "killshot", "odin", "claude_overseer") else "disabled", "reason": ""}
            continue
        agent_scan = _agents_raw.get(name)
        if agent_scan is True:
            agents[name] = {"status": "healthy", "reason": ""}
        elif agent_scan is False:
            agents[name] = {"status": "stopped", "reason": ""}
        elif isinstance(agent_scan, dict):
            is_running = agent_scan.get("running", False)
            agents[name] = {"status": "healthy" if is_running else "stopped", "reason": ""}
        else:
            agents[name] = {"status": "unknown", "reason": ""}

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
    _load(config.MAX_STATUS_FILE, {})
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
    import sys as _sys
    _sys.path.insert(0, str(Path.home() / "shared"))
    try:
        from finances import get_monthly_summary, get_alerts, _load as _fin_load
        fin_summary = get_monthly_summary()
        fin_data = _fin_load()
        fin_subs = [s for s in fin_data.get("subscriptions", []) if s.get("status") == "active"]
        fin_summary["active_count"] = len(fin_subs)
        fin_alerts = get_alerts()
        # Ensure agency and max project cards always show
        for p in ("agency", "max"):
            if p not in fin_summary.get("by_project", {}):
                fin_summary.setdefault("by_project", {})[p] = {"costs": 0, "revenue": 0, "net": 0}
    except Exception:
        fin_summary = {"month": "2026-03", "total_costs": 0, "total_revenue": 0,
                       "net": 0, "total_subscriptions": 0, "total_api": 0,
                       "total_one_time": 0, "active_count": 0, "by_project": {}}
        fin_subs = []
        fin_alerts = []


    # -- Leads Pipeline (outreach queue) --
    _pm_data = Path.home() / "polymarket-bot" / "data"
    outreach_raw = _load(_pm_data / "outreach_queue.json", [])
    outreach_seq = _load(_pm_data / "outreach_sequences.json", [])
    if not isinstance(outreach_raw, list):
        outreach_raw = []
    if not isinstance(outreach_seq, list):
        outreach_seq = []
    _oc = {}
    for _l in outreach_raw:
        _s = _l.get("status", "unknown")
        _oc[_s] = _oc.get(_s, 0) + 1
    outreach_stats = {
        "total": len(outreach_raw),
        "approved": _oc.get("approved", 0),
        "sent": _oc.get("sent", 0),
        "declined": _oc.get("declined", 0),
        "needs_contact": _oc.get("needs_contact_name", 0),
        "sequences": len(outreach_seq),
        "seq_paused": sum(1 for s in outreach_seq if s.get("status") == "paused"),
        "stages": _oc,
    }
    _niche_counts = {}
    for _l in outreach_raw:
        _n = _l.get("niche", "unknown")
        _niche_counts[_n] = _niche_counts.get(_n, 0) + 1
    outreach_stats["by_niche"] = dict(sorted(_niche_counts.items(), key=lambda x: -x[1]))
    # Top leads table (sent + approved, sorted by score)
    outreach_table = []
    for _l in outreach_raw:
        if _l.get("status") in ("sent", "approved"):
            _pd = _l.get("prospect_data", {}) or {}
            outreach_table.append({
                "name": _l.get("business_name", "?"),
                "niche": _l.get("niche", "?"),
                "city": _pd.get("city", ""),
                "state": _pd.get("state", ""),
                "score": _l.get("score", 0),
                "contact": _l.get("contact_name", ""),
                "email": _l.get("email", ""),
                "status": _l.get("status", ""),
                "demo_url": _l.get("demo_url", ""),
            })
    outreach_table.sort(key=lambda x: x.get("score", 0), reverse=True)

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
        outreach=outreach_stats,
        outreach_table=outreach_table,
    )


@app.route("/api/status")
def api_status():
    """JSON API for other agents."""
    if config is None:
        return jsonify({"error": "API-only mode"}), 503
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
    if config is None:
        return jsonify({"error": "API-only mode"}), 503
    import sys as _sys
    _sys.path.insert(0, str(Path.home() / "shared"))
    try:
        from finances import get_monthly_summary, get_alerts, get_upcoming_renewals, _load as _fin_load
        data = _fin_load()
        return {
            "subscriptions": data.get("subscriptions", []),
            "api_costs": data.get("api_costs", []),
            "one_time_costs": data.get("one_time_costs", []),
            "revenue": data.get("revenue", []),
            "summary": get_monthly_summary(),
            "alerts": get_alerts(),
            "upcoming_renewals": get_upcoming_renewals(),
        }
    except Exception as e:
        return {"error": str(e)}, 500




# ── ROI Calculator Subscribe Endpoint ──────────────────────────────
@app.route("/api/roi-subscribe", methods=["POST"])
def roi_subscribe():
    """Add email from ROI Calculator to MailerLite for nurture sequence."""
    import requests as _req
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()

    if not email or "@" not in email:
        return jsonify({"error": "invalid email"}), 400

    api_key = os.environ.get("MAILERLITE_API_KEY", "")
    if not api_key:
        # Log the lead locally even without MailerLite
        _log_roi_lead(email, data)
        return jsonify({"status": "logged"}), 200

    try:
        resp = _req.post(
            "https://connect.mailerlite.com/api/subscribers",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "email": email,
                "fields": {
                    "company": data.get("niche", ""),
                    "z_missed_calls": str(data.get("missed_calls", "")),
                    "z_client_value": str(data.get("client_value", "")),
                    "z_monthly_impact": data.get("monthly_impact", ""),
                },
                "groups": [],  # Add group ID later if needed
            },
            timeout=10,
        )
        _log_roi_lead(email, data, mailerlite_ok=resp.status_code in (200, 201))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        _log_roi_lead(email, data, error=str(e))
        return jsonify({"status": "logged"}), 200


def _log_roi_lead(email, data, mailerlite_ok=False, error=""):
    """Log ROI calculator lead to file."""
    import json
    from datetime import datetime
    log_path = os.path.join(os.path.dirname(__file__), "data", "roi_leads.jsonl")
    record = {
        "ts": datetime.utcnow().isoformat(),
        "email": email,
        "niche": data.get("niche", ""),
        "missed_calls": data.get("missed_calls"),
        "client_value": data.get("client_value"),
        "monthly_impact": data.get("monthly_impact", ""),
        "mailerlite": mailerlite_ok,
        "error": error,
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(record) + "\n")





# ── Outreach Queue API (War Room) ──────────────────────────────────

_QUEUE_PATH = os.path.join(os.path.expanduser("~"), "polymarket-bot", "data", "outreach_queue.json")
_INSTANTLY_WARMUP_START = "2026-03-15"
_INSTANTLY_WARMUP_DAYS = 21

def _load_outreach_queue():
    import json
    if os.path.exists(_QUEUE_PATH):
        try:
            with open(_QUEUE_PATH) as f:
                return json.load(f)
        except Exception:
            return []
    return []

def _save_outreach_queue(queue):
    import json
    with open(_QUEUE_PATH, "w") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)


@app.route("/api/queue")
def api_queue():
    """Get full outreach queue with stats."""
    import json
    from datetime import datetime, timedelta
    queue = _load_outreach_queue()

    # Classify statuses
    ready = [l for l in queue if l.get("status") in ("approved", "lead_approved") and l.get("email") and l.get("subject")]
    needs_fix = [l for l in queue if l.get("status") in ("approved", "lead_approved") and (not l.get("email") or not l.get("subject"))]
    held = [l for l in queue if l.get("status") == "needs_contact_name"]
    sent = [l for l in queue if l.get("status") == "sent"]
    pending_gate1 = [l for l in queue if l.get("status") == "pending"]

    # Niche breakdown
    niche_map = {"dental": 0, "dental practice": 0, "real estate": 0, "commercial real estate": 0,
                 "HVAC contractor": 0, "hvac": 0, "legal": 0, "personal injury lawyer": 0, "med spa": 0}
    for l in ready:
        n = l.get("niche", "other").lower()
        for k in niche_map:
            if k in n:
                niche_map[k] += 1
                break

    # Normalize niche counts
    niche_counts = {
        "dental": niche_map.get("dental", 0) + niche_map.get("dental practice", 0),
        "real_estate": niche_map.get("real estate", 0) + niche_map.get("commercial real estate", 0),
        "hvac": niche_map.get("HVAC contractor", 0) + niche_map.get("hvac", 0),
        "legal": niche_map.get("legal", 0) + niche_map.get("personal injury lawyer", 0),
        "med_spa": niche_map.get("med spa", 0),
    }

    # Instantly warmup countdown
    warmup_start = datetime.strptime(_INSTANTLY_WARMUP_START, "%Y-%m-%d")
    warmup_end = warmup_start + timedelta(days=_INSTANTLY_WARMUP_DAYS)
    now = datetime.utcnow()
    remaining = (warmup_end - now).total_seconds()
    warmup_ready = remaining <= 0
    days_left = max(0, int(remaining // 86400))
    hours_left = max(0, int((remaining % 86400) // 3600))

    # Build batches of 50 by niche
    batches = []
    from collections import defaultdict
    by_niche = defaultdict(list)
    for l in ready:
        n = l.get("niche", "other")
        by_niche[n].append(l)

    batch_id = 1
    for niche_name, leads in by_niche.items():
        for i in range(0, len(leads), 50):
            chunk = leads[i:i+50]
            personal_emails = sum(1 for l in chunk if l.get("email", "").split("@")[0] not in ("info", "contact", "hello", "office", "admin", "support"))
            info_emails = len(chunk) - personal_emails
            cities = list(set(l.get("city", "?") for l in chunk))
            avg_score = round(sum(l.get("score", 0) for l in chunk) / len(chunk), 1) if chunk else 0
            batches.append({
                "batch_id": batch_id,
                "niche": niche_name,
                "count": len(chunk),
                "cities": cities[:5],
                "avg_score": avg_score,
                "personal_emails": personal_emails,
                "info_emails": info_emails,
                "lead_ids": [l.get("id") for l in chunk],
            })
            batch_id += 1

    # Build lead list for table (ready + needs_fix + held)
    table_leads = []
    for l in ready + needs_fix + held + pending_gate1:
        email = l.get("email", "")
        is_personal = email and email.split("@")[0] not in ("info", "contact", "hello", "office", "admin", "support")

        # Determine display status
        status = "READY"
        if l.get("status") == "needs_contact_name":
            status = "HELD"
        elif l.get("status") == "pending":
            status = "PENDING"
        elif not email or not l.get("subject"):
            status = "EMAIL NEEDS FIX"
        elif not l.get("demo_url"):
            status = "DEMO NEEDS FIX"

        opener = (l.get("body", "") or "")[:120]

        table_leads.append({
            "id": l.get("id", ""),
            "business_name": l.get("business_name", "Unknown"),
            "niche": l.get("niche", "other"),
            "city": l.get("city", ""),
            "score": l.get("score", 0),
            "contact_name": l.get("contact_name", ""),
            "email": email,
            "is_personal_email": is_personal,
            "demo_url": l.get("demo_url", ""),
            "website": l.get("prospect_data", {}).get("website", ""),
            "subject": l.get("subject", ""),
            "body": l.get("body", ""),
            "opener": opener,
            "queued_at": l.get("queued_at", ""),
            "status": status,
        })

    return jsonify({
        "stats": {
            "total": len(ready) + len(needs_fix) + len(held) + len(pending_gate1),
            "ready": len(ready),
            "needs_fix": len(needs_fix),
            "held": len(held),
            "pending": len(pending_gate1),
            "sent": len(sent),
            "niche_breakdown": niche_counts,
        },
        "warmup": {
            "start": _INSTANTLY_WARMUP_START,
            "end": warmup_end.strftime("%Y-%m-%d"),
            "days_left": days_left,
            "hours_left": hours_left,
            "ready": warmup_ready,
        },
        "batches": batches,
        "leads": table_leads,
    })


@app.route("/api/queue/remove", methods=["POST"])
def api_queue_remove():
    """Remove a lead from the queue."""
    data = request.get_json(silent=True) or {}
    lead_id = data.get("id", "")
    if not lead_id:
        return jsonify({"error": "missing id"}), 400

    queue = _load_outreach_queue()
    queue = [l for l in queue if l.get("id") != lead_id]
    _save_outreach_queue(queue)
    return jsonify({"status": "removed"})


@app.route("/api/queue/flag", methods=["POST"])
def api_queue_flag():
    """Flag a lead for email rewrite."""
    data = request.get_json(silent=True) or {}
    lead_id = data.get("id", "")
    if not lead_id:
        return jsonify({"error": "missing id"}), 400

    queue = _load_outreach_queue()
    for l in queue:
        if l.get("id") == lead_id:
            l["status"] = "needs_rewrite"
            break
    _save_outreach_queue(queue)
    return jsonify({"status": "flagged"})


@app.route("/api/queue/priority", methods=["POST"])
def api_queue_priority():
    """Move a lead to priority (sends first)."""
    data = request.get_json(silent=True) or {}
    lead_id = data.get("id", "")
    if not lead_id:
        return jsonify({"error": "missing id"}), 400

    queue = _load_outreach_queue()
    for l in queue:
        if l.get("id") == lead_id:
            l["priority"] = True
            break
    _save_outreach_queue(queue)
    return jsonify({"status": "prioritized"})


@app.route("/api/queue/approve-batch", methods=["POST"])
def api_queue_approve_batch():
    """Approve a batch of leads — move to Gate 2."""
    data = request.get_json(silent=True) or {}
    lead_ids = data.get("lead_ids", [])
    if not lead_ids:
        return jsonify({"error": "missing lead_ids"}), 400

    queue = _load_outreach_queue()
    approved = 0
    for l in queue:
        if l.get("id") in lead_ids:
            l["status"] = "approved"
            l["batch_approved_at"] = __import__("datetime").datetime.utcnow().isoformat()
            approved += 1
    _save_outreach_queue(queue)
    return jsonify({"status": "batch_approved", "count": approved})


# ── Scan Tracker ──────────────────────────────────────────────────────

_SCAN_TRACKER_PATH = Path.home() / "polymarket-bot" / "data" / "scan_tracker.json"

# Exclusion zones — combos where emails have ALREADY been sent. DO NOT RESCAN.
_EXCLUSION_ZONES = {
    "dental": {
        "NH": ["ALL"],  # all NH cities
        "ME": ["Portland ME", "Bangor ME", "Augusta ME", "Waterville ME", "Rockland ME", "Lewiston ME"],
        "MA": ["Boston MA", "Cambridge MA", "Springfield MA", "Lowell MA"],
    },
    "real_estate": {
        "NH": ["ALL"],
        "ME": ["Portland ME", "Bangor ME", "Waterville ME", "Rockland ME", "Lewiston ME"],
        "MA": ["Boston MA", "Cambridge MA", "Springfield MA", "Lowell MA"],
    },
    "commercial_re": {
        "ME": ["Portland ME"],
        "NH": ["Portsmouth NH", "Concord NH"],
        "MA": ["Lowell MA"],
    },
}

# Niche name normalization
_NICHE_MAP = {
    "dental practice": "dental",
    "dental": "dental",
    "real estate": "real_estate",
    "commercial real estate": "commercial_re",
    "HVAC contractor": "hvac",
    "hvac": "hvac",
    "personal injury lawyer": "pi_lawyer",
    "med spa": "med_spa",
}

_DISPLAY_NICHES = ["dental", "real_estate", "hvac", "pi_lawyer", "med_spa", "commercial_re"]

# 500-lead schedule
_SCAN_SCHEDULE = [
    {"day": "Sun Mar 15", "niches": ["dental", "real_estate", "hvac", "pi_lawyer", "med_spa"],
     "cities": ["Hartford CT", "New Haven CT", "Stamford CT", "Bridgeport CT"], "est_leads": 140},
    {"day": "Mon Mar 16", "niches": ["dental", "real_estate", "hvac", "pi_lawyer", "med_spa"],
     "cities": ["Albany NY", "Syracuse NY", "Burlington VT", "Warwick RI"], "est_leads": 140},
    {"day": "Tue Mar 17", "niches": ["hvac", "pi_lawyer", "med_spa"],
     "cities": ["Cambridge MA", "Lowell MA", "Springfield MA", "Cranston RI"], "est_leads": 105},
    {"day": "Wed Mar 18", "niches": ["hvac", "pi_lawyer", "med_spa"],
     "cities": ["Fill gaps — any combos under target"], "est_leads": 70},
]


@app.route("/api/scan-tracker")
def api_scan_tracker():
    """Scan tracker — grid of niche x city with status, stats, schedule, exclusions."""
    queue = _load_outreach_queue()
    tracker = _load(_SCAN_TRACKER_PATH, {"completed_scans": []})
    completed = tracker.get("completed_scans", [])

    # Build cells from outreach queue
    cells = {}
    all_cities = set()
    for r in queue:
        raw_niche = r.get("niche", "")
        niche = _NICHE_MAP.get(raw_niche, raw_niche.lower().replace(" ", "_"))
        city = r.get("city", "")
        if not city or not niche:
            continue
        all_cities.add(city)
        key = f"{niche}|{city}"
        if key not in cells:
            cells[key] = {"sent": 0, "queued": 0, "declined": 0, "pending": 0, "total": 0}
        cells[key]["total"] += 1
        status = r.get("status", "")
        if status == "sent":
            cells[key]["sent"] += 1
        elif status in ("lead_approved", "approved"):
            cells[key]["queued"] += 1
        elif status == "declined":
            cells[key]["declined"] += 1
        elif status == "pending":
            cells[key]["pending"] += 1

    # Add scanned-but-no-leads combos from tracker
    for scan in completed:
        raw_niche = scan.get("niche", "")
        niche = _NICHE_MAP.get(raw_niche, raw_niche.lower().replace(" ", "_"))
        city = scan.get("city", "")
        if not city or not niche:
            continue
        all_cities.add(city)
        key = f"{niche}|{city}"
        if key not in cells:
            cells[key] = {"sent": 0, "queued": 0, "declined": 0, "pending": 0, "total": 0}

    # Determine cell status
    for key, cell in cells.items():
        if cell["sent"] > 0:
            cell["status"] = "SENT"
        elif cell["queued"] > 0:
            cell["status"] = "QUEUED"
        elif cell["total"] > 0:
            cell["status"] = "SCANNED"
        else:
            cell["status"] = "SCANNED"

    # Sort cities by state
    def city_sort_key(c):
        parts = c.rsplit(" ", 1)
        state = parts[-1] if len(parts) > 1 else ""
        return (state, c)

    sorted_cities = sorted(all_cities, key=city_sort_key)

    # Stats
    total_queued = sum(1 for r in queue if r.get("status") in ("lead_approved", "approved"))
    total_sent = sum(1 for r in queue if r.get("status") == "sent")
    total_pending = sum(1 for r in queue if r.get("status") == "pending")
    total_declined = sum(1 for r in queue if r.get("status") == "declined")
    target = 500

    # Build exclusion list for display
    exclusion_list = []
    for niche, states in _EXCLUSION_ZONES.items():
        for state, cities in states.items():
            if cities == ["ALL"]:
                exclusion_list.append({"niche": niche, "zone": f"ALL of {state}", "reason": "emails already sent"})
            else:
                for c in cities:
                    exclusion_list.append({"niche": niche, "zone": c, "reason": "emails already sent"})

    return jsonify({
        "grid": {
            "niches": _DISPLAY_NICHES,
            "cities": sorted_cities,
            "cells": cells,
        },
        "stats": {
            "total_leads": total_queued + total_pending,
            "total_sent": total_sent,
            "total_declined": total_declined,
            "total_queued": total_queued,
            "total_pending": total_pending,
            "target": target,
            "progress_pct": round((total_queued + total_pending) / target * 100, 1) if target > 0 else 0,
            "total_scanned_cities": len(all_cities),
        },
        "schedule": _SCAN_SCHEDULE,
        "exclusions": exclusion_list,
    })


# ── Website Grader API ─────────────────────────────────────────────
# Added to dashboard.py for darkcode-roi.onrender.com

import re
import html as _html
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

# ── CORS ──

@app.after_request
def add_cors_headers(response):
    """Allow requests from GitHub Pages and localhost."""
    origin = request.headers.get("Origin", "")
    allowed = (
        "https://darkcode-ai.github.io",
        "https://darkcodeai.com",
        "https://www.darkcodeai.com",
        "http://localhost",
        "http://127.0.0.1",
    )
    if any(origin.startswith(a) for a in allowed):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response


# ── Grader checks ──

_CHAT_SIGNATURES = [
    "intercom", "drift", "tidio", "tawk", "crisp.chat", "hubspot",
    "livechat", "zendesk", "freshdesk", "olark", "smartsupp",
    "chaport", "jivochat", "comm100", "purechat", "chatbot",
    "messenger.com", "fb-messenger", "whatsapp.com/send",
]

_BOOKING_SIGNATURES = [
    "calendly.com", "acuityscheduling.com", "square.site",
    "booksy.com", "schedulicity.com", "vagaro.com", "mindbodyonline.com",
    "setmore.com", "simplybook.me", "zoho.com/bookings",
    "book-online", "book-now", "schedule-appointment", "book-appointment",
]

_FORM_SIGNATURES = [
    "<form", "input[type=\"email\"]", "input[type=email]",
    "typeform.com", "jotform.com", "google.com/forms", "formspree",
    "hubspot", "contact-form", "wpcf7", "wpforms", "gravityforms",
]

_REVIEW_SIGNATURES = [
    "google.com/maps/contrib", "yelp.com", "trustpilot.com",
    "bbb.org", "healthgrades.com", "zocdoc.com", "avvo.com",
    "testimonial", "review", "rating", "stars",
]

_SOCIAL_PLATFORMS = {
    "facebook": ["facebook.com/", "fb.com/"],
    "instagram": ["instagram.com/"],
    "twitter": ["twitter.com/", "x.com/"],
    "linkedin": ["linkedin.com/"],
    "youtube": ["youtube.com/", "youtu.be/"],
}


def _fetch_html(url):
    """Fetch page HTML with a reasonable timeout."""
    import requests as _req
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    resp = _req.get(url, headers=headers, timeout=15, allow_redirects=True, verify=False)
    return resp.text, resp.url


def _fetch_pagespeed(url):
    """Call Google PageSpeed Insights API (free, no key needed)."""
    import requests as _req
    results = {}
    for strategy in ("desktop", "mobile"):
        try:
            resp = _req.get(
                "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                params={"url": url, "strategy": strategy, "category": "performance"},
                timeout=30,
            )
            data = resp.json()
            score = data.get("lighthouseResult", {}).get("categories", {}).get("performance", {}).get("score")
            if score is not None:
                results[strategy] = round(score * 100)
        except Exception:
            pass
    return results


def _check_chat(html_lower):
    """Check 1: Live Chat / Chatbot (20 pts)."""
    found = [s for s in _CHAT_SIGNATURES if s in html_lower]
    if found:
        return {"pass": True, "score": 20, "max": 20, "detail": f"Found: {', '.join(found[:3])}", "fix": ""}
    return {
        "pass": False, "score": 0, "max": 20,
        "detail": "Visitors can't get help after hours — you're losing leads while you sleep",
        "fix": "Add a live chat widget or AI chatbot to capture leads 24/7",
    }


def _check_speed(pagespeed):
    """Check 2: Page Speed (15 pts)."""
    desktop = pagespeed.get("desktop")
    if desktop is None:
        return {"pass": False, "score": 5, "max": 15, "detail": "Could not measure page speed", "fix": "Optimize images, enable caching, and minimize JavaScript"}
    pts = round(desktop / 100 * 15)
    if desktop >= 70:
        return {"pass": True, "score": pts, "max": 15, "detail": f"Desktop speed score: {desktop}/100", "fix": ""}
    return {
        "pass": False, "score": pts, "max": 15,
        "detail": f"Your site takes too long to load (score: {desktop}/100) — visitors leave before it opens",
        "fix": "Compress images, remove unused scripts, and enable browser caching",
    }


def _check_mobile(pagespeed):
    """Check 3: Mobile Responsive (15 pts)."""
    mobile = pagespeed.get("mobile")
    if mobile is None:
        return {"pass": False, "score": 5, "max": 15, "detail": "Could not measure mobile performance", "fix": "Ensure your site is mobile-responsive"}
    pts = round(mobile / 100 * 15)
    if mobile >= 50:
        return {"pass": True, "score": pts, "max": 15, "detail": f"Mobile performance score: {mobile}/100", "fix": ""}
    return {
        "pass": False, "score": pts, "max": 15,
        "detail": f"Your site doesn't work well on phones (score: {mobile}/100) — that's where most customers browse",
        "fix": "Use responsive design, optimize images for mobile, reduce JavaScript",
    }


def _check_form(html_lower):
    """Check 4: Contact Form (10 pts)."""
    found = [s for s in _FORM_SIGNATURES if s in html_lower]
    if found:
        return {"pass": True, "score": 10, "max": 10, "detail": "Contact form detected", "fix": ""}
    return {
        "pass": False, "score": 0, "max": 10,
        "detail": "No easy way to reach you — visitors won't pick up the phone",
        "fix": "Add a contact form so visitors can reach you in seconds",
    }


def _check_phone(html_lower):
    """Check 5: Phone Number Visible (8 pts)."""
    has_tel = "tel:" in html_lower
    phone_regex = re.search(r'[\(]?\d{3}[\)\-\.\s]?\s?\d{3}[\-\.\s]?\d{4}', html_lower)
    if has_tel or phone_regex:
        return {"pass": True, "score": 8, "max": 8, "detail": "Phone number found", "fix": ""}
    return {
        "pass": False, "score": 0, "max": 8,
        "detail": "Your phone number isn't easy to find — customers give up",
        "fix": "Add your phone number in the header or footer with a clickable tel: link",
    }


def _check_ssl(final_url):
    """Check 6: SSL/HTTPS (7 pts)."""
    if final_url.startswith("https://"):
        return {"pass": True, "score": 7, "max": 7, "detail": "Site uses HTTPS", "fix": ""}
    return {
        "pass": False, "score": 0, "max": 7,
        "detail": "Your site shows 'Not Secure' in browsers — visitors don't trust it",
        "fix": "Install an SSL certificate (most hosts offer free Let's Encrypt)",
    }


def _check_booking(html_lower):
    """Check 7: Online Booking (8 pts)."""
    found = [s for s in _BOOKING_SIGNATURES if s in html_lower]
    if found:
        return {"pass": True, "score": 8, "max": 8, "detail": f"Booking detected: {', '.join(found[:2])}", "fix": ""}
    return {
        "pass": False, "score": 0, "max": 8,
        "detail": "Customers can't book appointments online — they'll go to a competitor who lets them",
        "fix": "Add online scheduling (Calendly, Acuity, or a built-in booking widget)",
    }


def _check_social(html_lower):
    """Check 8: Social Media Links (5 pts)."""
    found = []
    for platform, patterns in _SOCIAL_PLATFORMS.items():
        if any(p in html_lower for p in patterns):
            found.append(platform)
    pts = min(5, len(found))
    if pts >= 3:
        return {"pass": True, "score": pts, "max": 5, "detail": f"Found: {', '.join(found)}", "fix": ""}
    return {
        "pass": len(found) > 0, "score": pts, "max": 5,
        "detail": f"{'Only ' + ', '.join(found) + ' found' if found else 'No social media presence linked'} — builds trust with potential customers",
        "fix": "Add links to your active social media profiles in the footer",
    }


def _check_maps(html_lower):
    """Check 9: Google Maps (5 pts)."""
    if "maps.google.com" in html_lower or "google.com/maps" in html_lower or "maps/embed" in html_lower:
        return {"pass": True, "score": 5, "max": 5, "detail": "Google Maps embed found", "fix": ""}
    return {
        "pass": False, "score": 0, "max": 5,
        "detail": "No map on your site — local customers can't find you easily",
        "fix": "Embed a Google Maps widget showing your business location",
    }


def _check_reviews(html_lower):
    """Check 10: Reviews/Testimonials (5 pts)."""
    found = [s for s in _REVIEW_SIGNATURES if s in html_lower]
    if found:
        return {"pass": True, "score": 5, "max": 5, "detail": "Reviews/testimonials section detected", "fix": ""}
    return {
        "pass": False, "score": 0, "max": 5,
        "detail": "No reviews or testimonials on your site — the #1 thing customers check",
        "fix": "Add a testimonials section or embed Google/Yelp reviews",
    }


def _check_seo(html_lower):
    """Check 11: SEO Meta Tags (2 pts)."""
    has_title = "<title>" in html_lower and "</title>" in html_lower
    has_desc = 'meta name="description"' in html_lower or "meta name='description'" in html_lower
    pts = (1 if has_title else 0) + (1 if has_desc else 0)
    if pts == 2:
        return {"pass": True, "score": 2, "max": 2, "detail": "Title and meta description present", "fix": ""}
    missing = []
    if not has_title:
        missing.append("title tag")
    if not has_desc:
        missing.append("meta description")
    return {
        "pass": False, "score": pts, "max": 2,
        "detail": f"Missing {', '.join(missing)} — search engines can't understand your page",
        "fix": "Add a descriptive <title> and <meta name='description'> tag",
    }


def _grade_from_score(score):
    if score >= 95: return "A+"
    if score >= 85: return "A"
    if score >= 70: return "B"
    if score >= 50: return "C"
    if score >= 30: return "D"
    return "F"


@app.route("/api/grade", methods=["POST", "OPTIONS"])
def api_grade():
    """Grade a website on 11 checks."""
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "URL required"}), 400

    # Normalize URL
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
        if not parsed.netloc or "." not in parsed.netloc:
            return jsonify({"error": "Invalid URL"}), 400
    except Exception:
        return jsonify({"error": "Invalid URL"}), 400

    try:
        # Fetch HTML and PageSpeed in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            html_future = executor.submit(_fetch_html, url)
            ps_future = executor.submit(_fetch_pagespeed, url)

            raw_html, final_url = html_future.result(timeout=20)
            pagespeed = ps_future.result(timeout=45)

        html_lower = raw_html.lower()

        # Run all 11 checks
        checks = [
            {"name": "Live Chat / Chatbot", **_check_chat(html_lower)},
            {"name": "Page Speed", **_check_speed(pagespeed)},
            {"name": "Mobile Responsive", **_check_mobile(pagespeed)},
            {"name": "Contact Form", **_check_form(html_lower)},
            {"name": "Phone Number Visible", **_check_phone(html_lower)},
            {"name": "SSL / HTTPS", **_check_ssl(final_url)},
            {"name": "Online Booking", **_check_booking(html_lower)},
            {"name": "Social Media Links", **_check_social(html_lower)},
            {"name": "Google Maps", **_check_maps(html_lower)},
            {"name": "Reviews / Testimonials", **_check_reviews(html_lower)},
            {"name": "SEO Meta Tags", **_check_seo(html_lower)},
        ]

        total_score = sum(c["score"] for c in checks)
        grade = _grade_from_score(total_score)

        # Top issues (failed checks sorted by max points desc)
        issues = sorted(
            [c for c in checks if not c["pass"]],
            key=lambda c: c["max"],
            reverse=True,
        )

        return jsonify({
            "url": url,
            "final_url": final_url,
            "score": total_score,
            "grade": grade,
            "checks": checks,
            "top_issues": [{"name": i["name"], "detail": i["detail"]} for i in issues[:3]],
        })

    except Exception as e:
        log.exception("Grade error for %s", url)
        return jsonify({"error": f"Could not scan website: {str(e)}"}), 500


@app.route("/api/grade-subscribe", methods=["POST", "OPTIONS"])
def grade_subscribe():
    """Capture email from Website Grader."""
    if request.method == "OPTIONS":
        return "", 204

    import requests as _req
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()

    if not email or "@" not in email:
        return jsonify({"error": "invalid email"}), 400

    # Log locally
    _log_grader_lead(email, data)

    # Push to MailerLite
    api_key = os.environ.get("MAILERLITE_API_KEY", "")
    if api_key:
        try:
            _req.post(
                "https://connect.mailerlite.com/api/subscribers",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "email": email,
                    "fields": {
                        "company": data.get("url", ""),
                        "z_website_grade": data.get("grade", ""),
                        "z_website_score": str(data.get("score", "")),
                    },
                    "groups": [],
                },
                timeout=10,
            )
        except Exception:
            pass

    return jsonify({"status": "ok"}), 200


def _log_grader_lead(email, data):
    """Log website grader lead to file."""
    from datetime import datetime
    log_path = os.path.join(os.path.dirname(__file__), "data", "grader_leads.jsonl")
    record = {
        "ts": datetime.utcnow().isoformat(),
        "email": email,
        "url": data.get("url", ""),
        "grade": data.get("grade", ""),
        "score": data.get("score", ""),
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(record) + "\n")


@app.route("/api/contact", methods=["POST", "OPTIONS"])
def api_contact():
    """Contact form submission from darkcodeai.com."""
    if request.method == "OPTIONS":
        return "", 204

    import requests as _req
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    url = data.get("url", "").strip()
    message = data.get("message", "").strip()

    if not email or "@" not in email or not name:
        return jsonify({"error": "Name and email required"}), 400

    # Log locally
    from datetime import datetime
    log_path = os.path.join(os.path.dirname(__file__), "data", "contact_leads.jsonl")
    record = {
        "ts": datetime.utcnow().isoformat(),
        "name": name,
        "email": email,
        "url": url,
        "message": message,
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(record) + "\n")

    # Push to MailerLite
    api_key = os.environ.get("MAILERLITE_API_KEY", "")
    if api_key:
        try:
            _req.post(
                "https://connect.mailerlite.com/api/subscribers",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "email": email,
                    "fields": {
                        "name": name,
                        "company": url,
                        "z_source": "contact_form",
                        "z_message": message[:200],
                    },
                    "groups": [],
                },
                timeout=10,
            )
        except Exception:
            pass

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8878, debug=False)
