import os, json, requests, subprocess, tempfile
from datetime import datetime, timezone

SHEET_ID = "3906472049069956"
SS_TOKEN = os.environ["SMARTSHEET_API_TOKEN"]
CF_ACCOUNT_ID = os.environ["CF_ACCOUNT_ID"]
CF_API_TOKEN = os.environ["CF_API_TOKEN"]
CF_PROJECT_NAME = "mytratimeline"

COLUMN_MAP = {
    8108061649227652: "statusEmoji",
    1582859742302084: "ryg",
    4507059511578500: "name",
    2255259697893252: "start",
    6758859325263748: "finish",
    7619163756121988: "duration",
    4201085181579140: "assignee",
    8704684808949636: "pctComplete",
    3115564128751492: "predecessors",
    1989664221908868: "comments",
    7348448918196100: "masterScheduleItem",
}

LOGO_B64 = "PHN2ZyB3aWR0aD0iMTA0OSIgaGVpZ2h0PSI0MjYiIHZpZXdCb3g9IjAgMCAxMDQ5IDQyNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTkwNC4zOTggMjQ2Ljk0MUw5MDQuNzAzIDI0Ni4xOThMOTE5LjI3NCAyMTEuODg0TDkzNC4wNTUgMjQ2LjE5OEg5MzQuMjA3TDkzOC42NyAyNTYuNDE1SDk2Mi4wNzFMOTIwLjk5MSAxNzAuMjg5QzkyMC42MDkgMTY5LjQxMiA5MTkuODg0IDE2OS40MTIgOTE5LjQ4NCAxNzAuMjg5TDg3OC4zMjcgMjU2LjQ3M0g5MDAuMzc0TDkwNC4zOTggMjQ2Ljk0MVoiIGZpbGw9ImJsYWNrIi8+CjxwYXRoIGQ9Ik03NzcuNDk1IDI1Ni40NzNINzU0LjgzOFYxNzEuNzc2SDc4OS4wNzFDODEwLjU4NCAxNzEuNzc2IDgyMi41NDIgMTg0LjQ1MyA4MjIuNTQyIDIwMS43NjJDODIyLjU0MiAyMTIuOTUyIDgxNy4yMDIgMjIxLjc3OCA4MDcuMTEzIDIyNi4zNzJMODI0LjY1OSAyNTYuMzc3SDgwMC4xMzNMNzg1LjIgMjI5Ljg4SDc3Ny41NzFMNzc3LjQ5NSAyNTYuNDczWk03ODcuOTQ2IDIxMi42MjhDNzk1LjU3NSAyMTIuNjI4IDc5OS43NzEgMjA4LjgxNSA3OTkuNzcxIDIwMS44Qzc5OS43NzEgMTk0Ljc4NSA3OTUuNjUxIDE5MC45NzIgNzg3Ljk0NiAxOTAuOTcySDc3Ny40OTVWMjEyLjYyOEg3ODcuOTQ2WiIgZmlsbD0iYmxhY2siLz4KPHBhdGggZD0iTTY0OS43NTMgMTkwLjgySDYyNy4zNjNWMTcxLjc3Nkg2OTQuODJWMTkwLjgySDY3Mi40M1YyNTYuMzc3SDY0OS43NTNWMTkwLjgyWiIgZmlsbD0iYmxhY2siLz4KPHBhdGggZD0iTTQ5Mi4xODMgMTcxLjc3Nkg1MTcuMDlMNTMzLjc1OSAyMDIuNzUzTDU1MC40NDYgMTcxLjc3Nkg1NzQuMjFMNTQ0LjcwNiAyMjMuMDM2VjI1Ni4zNzdINTIyLjA2OFYyMjMuNjY1TDQ5Mi4xODMgMTcxLjc3NloiIGZpbGw9ImJsYWNrIi8+CjxwYXRoIGQ9Ik0zNTMuMzk4IDE3MC44OTlDMzUzLjUxMiAxNzAuMDQxIDM1NC4wMDggMTcwLjE1NiAzNTQuNTA0IDE3MC43ODVMMzk1LjA3IDIxNi4zMDdMNDM1LjEyIDE3MC43ODVDNDM1LjYxNiAxNzAuMTU2IDQzNi4xMTIgMTcwLjA0MSA0MzYuMjQ1IDE3MC44OTlMNDQxLjE0NyAyNTYuNDczSDQxOC44NTJMNDE2Ljk0NSAyMjAuMzg2TDM5NS43OTQgMjQ0LjkwMUMzOTUuNzI2IDI0NC45ODUgMzk1LjY0MSAyNDUuMDUzIDM5NS41NDMgMjQ1LjA5OUMzOTUuNDQ2IDI0NS4xNDUgMzk1LjMzOSAyNDUuMTY5IDM5NS4yMzIgMjQ1LjE2OUMzOTUuMTI0IDI0NS4xNjkgMzk1LjAxNyAyNDUuMTQ1IDM5NC45MiAyNDUuMDk5QzM5NC44MjMgMjQ1LjA1MyAzOTQuNzM3IDI0NC45ODUgMzk0LjY2OSAyNDQuOTAxTDM3Mi41NjUgMjIwLjI1M0wzNzAuNjU4IDI1Ni40NzNIMzQ4LjQ3OEwzNTMuMzk4IDE3MC44OTlaIiBmaWxsPSJibGFjayIvPgo8cGF0aCBkPSJNOTc0LjYzMyAyNTdWMjY5SDk3Mi4zNTdWMjU3SDk3NC42MzNaTTk3OC4wNDQgMjU3VjI1OC45MzdIOTY5VjI1N0g5NzguMDQ0WiIgZmlsbD0iYmxhY2siLz4KPHBhdGggZD0iTTk4MC4zODggMjU3SDk4Mi4zMjJMOTg1LjE2OSAyNjUuODFMOTg4LjAxNiAyNTdIOTg5Ljk0OUw5ODUuOTQ1IDI2OUg5ODQuMzkyTDk4MC4zODggMjU3Wk05NzkuMzQ1IDI1N0g5ODEuMjcxTDk4MS42MjEgMjY1LjU4OFYyNjlIOTc5LjM0NVYyNTdaTTk4OS4wNjYgMjU3SDk5MVYyNjlIOTg4LjcxNlYyNjUuNTg4TDk4OS4wNjYgMjU3WiIgZmlsbD0iYmxhY2siLz4KPHBhdGggZD0iTTg4LjAxNTYgMTQwLjYyN1YyODUuMzcyQzg4LjE0NjkgMjg4LjQzNiA4OS4yNzM0IDI5MS4zNzQgOTEuMjI0NyAyOTMuNzRDOTMuMTc1OSAyOTYuMTA3IDk1Ljg0NTYgMjk3Ljc3MyA5OC44Mjk0IDI5OC40ODdMMTE0LjA4NyAzMDIuODUzVjE1Ni42NEMxMTQuMDg3IDE1My4zMDQgMTE4LjY4MyAxNTEuNjQ2IDEyMS4zNTMgMTU0LjAwOUwxNDQuOTQ1IDE3NC45NzlDMTQ1LjMyNSAxNzUuMzAxIDE0NS42MzIgMTc1LjcgMTQ1Ljg0NiAxNzYuMTUxQzE0Ni4wNiAxNzYuNjAxIDE0Ni4xNzUgMTc3LjA5MiAxNDYuMTg0IDE3Ny41OVYzMTIuMDc5TDE3Ny43NDggMzIxLjE5MVYxNDQuMTkyQzE3Ny43NDggMTQxLjAyNyAxODEuOTYzIDEzOS4zMTIgMTg0LjcyOCAxNDEuMzMyTDIxNS4yNDMgMTYzLjY1NUMyMTUuNzA2IDE2My45NzYgMjE2LjA4NiAxNjQuNDAzIDIxNi4zNTIgMTY0LjlDMjE2LjYxNyAxNjUuMzk4IDIxNi43NiAxNjUuOTUxIDIxNi43NjkgMTY2LjUxNVYzMzIuNDU4TDIzNy40OCAzMzguNDI0QzI0Ny42NjUgMzQxLjM2IDI1OC4xMzUgMzM0LjYxMiAyNTguMTM1IDMyNS4zMDlWMTAwLjY5QzI1OC4xMzUgOTEuMjkyMiAyNDcuNjY1IDg0LjYzOTIgMjM3LjQ4IDg3LjU3NDlMOTguODg2NCAxMjcuNjA3Qzk1LjkwMjcgMTI4LjMyMSA5My4yMzMyIDEyOS45ODggOTEuMjgxOSAxMzIuMzU0Qzg5LjMzMDcgMTM0LjcyMSA4OC4yMDQxIDEzNy42NTkgODguMDcyOSAxNDAuNzIyIiBmaWxsPSJibGFjayIvPgo8L3N2Zz4K"


def normalize_date(val):
    if not val:
        return None
    if "T" in str(val):
        return str(val).split("T")[0]
    return str(val)


def fetch_rows():
    resp = requests.get(
        f"https://api.smartsheet.com/2.0/sheets/{SHEET_ID}",
        headers={"Authorization": f"Bearer {SS_TOKEN}"}
    )
    resp.raise_for_status()
    sheet = resp.json()
    rows = []
    for row in sheet["rows"]:
        node = {
            "id": str(row["id"]),
            "parentId": str(row["parentId"]) if row.get("parentId") else None,
        }
        for cell in row.get("cells", []):
            field = COLUMN_MAP.get(cell["columnId"])
            if not field:
                continue
            val = cell.get("displayValue") if cell.get("displayValue") is not None else cell.get("value")
            if field in ("start", "finish"):
                val = normalize_date(val)
            node[field] = val
        rows.append(node)
    return rows


def build_html(rows, updated_at):
    data_json = json.dumps({"updatedAt": updated_at, "rows": rows}, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mytra Timeline</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}

:root[data-theme="dark"]{{
  --bg:#0f0f13;--bg2:#16161d;--bg3:#1e1e28;--border:#2a2a38;
  --text:#e8e8f0;--text2:#9090a8;--text3:#5a5a72;
  --accent:rgb(85,53,243);--accent-light:rgba(85,53,243,0.25);
  --ryg-green:#22c55e;--ryg-yellow:#eab308;--ryg-red:#ef4444;
  --ryg-gray:#6b7280;--ryg-done:#5535f3;
  --bar:rgb(85,53,243);--bar-pct:rgba(255,255,255,0.25);
  --tooltip-bg:#1e1e28;--panel-bg:#16161d;
}}
:root[data-theme="light"]{{
  --bg:#f4f4f8;--bg2:#ffffff;--bg3:#ebebf2;--border:#d0d0e0;
  --text:#1a1a2e;--text2:#555570;--text3:#9090a8;
  --accent:rgb(85,53,243);--accent-light:rgba(85,53,243,0.12);
  --ryg-green:#16a34a;--ryg-yellow:#ca8a04;--ryg-red:#dc2626;
  --ryg-gray:#4b5563;--ryg-done:#5535f3;
  --bar:rgb(85,53,243);--bar-pct:rgba(255,255,255,0.4);
  --tooltip-bg:#ffffff;--panel-bg:#ffffff;
}}

html,body{{height:100%;background:var(--bg);color:var(--text);font-family:'Roboto Mono',monospace;font-size:12px;overflow:hidden}}

#toolbar{{display:flex;align-items:center;gap:8px;padding:6px 12px;background:var(--bg2);border-bottom:1px solid var(--border);flex-shrink:0;flex-wrap:wrap}}
#toolbar-logo{{height:28px;display:block;filter:invert(1);margin-right:8px}}
:root[data-theme="light"] #toolbar-logo{{filter:invert(0)}}
.tb-sep{{width:1px;height:20px;background:var(--border);margin:0 4px}}
.btn{{background:var(--bg3);border:1px solid var(--border);color:var(--text2);padding:3px 8px;border-radius:4px;cursor:pointer;font-size:11px;font-family:'Roboto Mono',monospace;transition:all .15s}}
.btn:hover{{border-color:var(--accent);color:var(--text)}}
.btn.active{{background:var(--accent-light);border-color:var(--accent);color:var(--accent)}}
.ryg-btn{{width:20px;height:20px;border-radius:50%;border:2px solid transparent;padding:0;position:relative;flex-shrink:0;transition:transform .15s,border-color .15s,opacity .15s}}
.ryg-btn:hover{{transform:scale(1.2);border-color:rgba(255,255,255,0.4) !important}}
.ryg-btn:not(.active){{opacity:0.25}}
.ryg-btn.active{{opacity:1;border-color:rgba(255,255,255,0.2)}}
#filter-include,#filter-exclude{{background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:3px 7px;border-radius:4px;font-size:11px;font-family:'Roboto Mono',monospace;width:120px}}
#filter-include::placeholder,#filter-exclude::placeholder{{color:var(--text3)}}
#updated{{margin-left:auto;color:var(--text3);font-size:10px;white-space:nowrap}}

#app{{display:flex;flex-direction:column;height:100vh}}
#gantt-wrap{{display:flex;flex:1;overflow:hidden;position:relative}}

#label-panel{{width:320px;min-width:200px;max-width:500px;flex-shrink:0;overflow-y:auto;overflow-x:hidden;border-right:1px solid var(--border);background:var(--bg2);position:relative}}
#label-header{{height:36px;display:flex;align-items:center;padding:0 8px;border-bottom:1px solid var(--border);background:var(--bg2);position:sticky;top:0;z-index:2;font-family:'Roboto',sans-serif;font-size:13px;font-weight:600;color:var(--text2);letter-spacing:.5px}}

.row-label{{display:flex;align-items:center;height:28px;padding-right:8px;cursor:pointer;border-bottom:1px solid var(--border);transition:background .1s;position:relative}}
.row-label:hover{{background:var(--bg3)}}
.row-label.selected{{background:var(--accent-light)}}
.row-label .chevron{{width:16px;flex-shrink:0;color:var(--text3);font-size:10px;text-align:center;user-select:none}}
.row-label .ryg-circle{{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-right:5px}}
.row-label .name{{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--text);font-size:11px}}
.row-label.group-row .name{{font-family:'Roboto',sans-serif;font-size:13px;font-weight:600;letter-spacing:.3px}}

#bars-wrap{{flex:1;overflow:auto;position:relative}}
#bars-inner{{position:relative}}
#time-axis{{height:36px;position:sticky;top:0;z-index:3;background:var(--bg2);border-bottom:1px solid var(--border)}}
#bars-svg{{display:block}}

#label-panel::-webkit-scrollbar,#bars-wrap::-webkit-scrollbar{{width:6px;height:6px}}
#label-panel::-webkit-scrollbar-track,#bars-wrap::-webkit-scrollbar-track{{background:var(--bg)}}
#label-panel::-webkit-scrollbar-thumb,#bars-wrap::-webkit-scrollbar-thumb{{background:var(--border);border-radius:3px}}

#tooltip{{position:fixed;pointer-events:none;background:var(--tooltip-bg);border:1px solid var(--border);border-radius:6px;padding:8px 10px;font-size:11px;z-index:9999;display:none;max-width:240px;box-shadow:0 4px 16px rgba(0,0,0,0.4)}}
#tooltip .tt-name{{font-family:'Roboto',sans-serif;font-size:14px;font-weight:600;color:var(--text);margin-bottom:5px;line-height:1.2}}
#tooltip .tt-row{{display:flex;gap:6px;color:var(--text2);margin-top:2px}}
#tooltip .tt-label{{color:var(--text3);min-width:55px}}

#detail-panel{{position:fixed;right:0;top:0;bottom:0;width:360px;background:var(--panel-bg);border-left:1px solid var(--border);z-index:50;transform:translateX(100%);transition:transform .25s ease;overflow-y:auto;padding:16px}}
#detail-panel.open{{transform:translateX(0)}}
#detail-close{{float:right;background:none;border:none;color:var(--text2);cursor:pointer;font-size:16px;padding:0 4px}}
#detail-panel h2{{font-family:'Roboto',sans-serif;font-size:18px;font-weight:700;color:var(--text);margin-bottom:12px;padding-right:24px;line-height:1.2}}
.detail-field{{margin-bottom:8px}}
.detail-label{{color:var(--text3);font-size:10px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px}}
.detail-value{{color:var(--text);font-size:12px;word-break:break-word}}

#resize-handle{{width:4px;cursor:col-resize;background:transparent;flex-shrink:0;transition:background .15s}}
#resize-handle:hover{{background:var(--accent)}}
</style>
</head>
<body>
<div id="app">
  <div id="toolbar">
    <img id="toolbar-logo" src="data:image/svg+xml;base64,{LOGO_B64}" alt="Mytra">
    <div class="tb-sep"></div>
    <button class="btn" data-tip="Collapse all" onclick="collapseAll()">− all</button>
    <button class="btn" data-tip="Collapse one level" onclick="changeLevel(-1)">−</button>
    <button class="btn" data-tip="Expand one level" onclick="changeLevel(1)">+</button>
    <button class="btn" data-tip="Expand all" onclick="expandAll()">+ all</button>
    <div class="tb-sep"></div>
    <button class="ryg-btn active" data-ryg="Green" data-tip="On track" onclick="toggleRYG(this)" style="background:var(--ryg-green)"></button>
    <button class="ryg-btn active" data-ryg="Yellow" data-tip="At risk" onclick="toggleRYG(this)" style="background:var(--ryg-yellow)"></button>
    <button class="ryg-btn active" data-ryg="Red" data-tip="Critical" onclick="toggleRYG(this)" style="background:var(--ryg-red)"></button>
    <button class="ryg-btn active" data-ryg="Gray" data-tip="No status" onclick="toggleRYG(this)" style="background:var(--ryg-gray)"></button>
    <div class="tb-sep"></div>
    <input id="filter-include" placeholder="include..." oninput="applyFilters()">
    <input id="filter-exclude" placeholder="exclude..." oninput="applyFilters()">
    <div class="tb-sep"></div>
    <button class="btn" data-scale="D" onclick="setScale(this)">Day</button>
    <button class="btn active" data-scale="W" onclick="setScale(this)">Week</button>
    <button class="btn" data-scale="M" onclick="setScale(this)">Month</button>
    <button class="btn" data-scale="Q" onclick="setScale(this)">Quarter</button>
    <div class="tb-sep"></div>
    <button class="btn" id="theme-btn" onclick="toggleTheme()" style="padding:3px 6px;line-height:0"></button>
    <span id="updated"></span>
  </div>
  <div id="gantt-wrap">
    <div id="label-panel">
      <div id="label-header">Task</div>
      <div id="label-rows"></div>
    </div>
    <div id="resize-handle"></div>
    <div id="bars-wrap">
      <div id="bars-inner">
        <div id="time-axis"></div>
        <svg id="bars-svg"></svg>
      </div>
    </div>
  </div>
</div>
<div id="tooltip"></div>
<div id="detail-panel">
  <button id="detail-close" onclick="closeDetail()">✕</button>
  <div id="detail-content"></div>
</div>

<script>
const __DATA__ = {data_json};
const ROWS = __DATA__.rows;
const ROW_H = 28;
const AXIS_H = 36;
const RYG_COLORS = {{Green:'#22c55e',Yellow:'#eab308',Red:'#ef4444',Gray:'#6b7280'}};
const RYG_DONE = '#5535f3';

let collapsed = new Set();
let visibleRYG = new Set(['Green','Yellow','Red','Gray']);
let currentScale = 'W';
let selectedId = null;
let rowMap = {{}};
let visibleRows = [];
let minDate, maxDate, totalDays, pxPerDay;

function init() {{
  ROWS.forEach(r => rowMap[r.id] = r);
  const d = new Date(__DATA__.updatedAt);
  document.getElementById('updated').textContent = 'Updated ' + d.toLocaleString();
  ROWS.forEach(r => {{ if (getDepth(r) >= 2) collapsed.add(r.id); }});
  computeDateRange();
  render();
  setupSync();
  setupResize();
  setupRygTips();
}}

function setupRygTips() {{
  document.querySelectorAll('[data-tip]').forEach(btn => {{
    btn.addEventListener('mouseenter', e => {{
      const tt = document.getElementById('tooltip');
      tt.innerHTML = `<div class="tt-name">${{btn.dataset.tip}}</div>`;
      tt.style.display = 'block';
      positionTooltip(e);
    }});
    btn.addEventListener('mousemove', positionTooltip);
    btn.addEventListener('mouseleave', hideTooltip);
  }});
}}

function positionTooltip(e) {{
  const tt = document.getElementById('tooltip');
  const x = e.clientX + 14, y = e.clientY + 14;
  tt.style.left = (x + tt.offsetWidth > window.innerWidth ? x - tt.offsetWidth - 20 : x) + 'px';
  tt.style.top = y + 'px';
}}

function getDepth(row) {{
  let d = 0, cur = row;
  while (cur.parentId && rowMap[cur.parentId]) {{ d++; cur = rowMap[cur.parentId]; }}
  return d;
}}

function isAncestorCollapsed(row) {{
  let cur = row;
  while (cur.parentId) {{
    if (collapsed.has(cur.parentId)) return true;
    cur = rowMap[cur.parentId] || {{}};
    if (!cur.id) break;
  }}
  return false;
}}

function hasChildren(id) {{ return ROWS.some(r => r.parentId === id); }}

function computeDateRange() {{
  let min = Infinity, max = -Infinity;
  ROWS.forEach(r => {{
    if (r.start) {{ const d = +new Date(r.start); if (d < min) min = d; }}
    if (r.finish) {{ const d = +new Date(r.finish); if (d > max) max = d; }}
  }});
  min -= 14 * 86400000;
  max += 14 * 86400000;
  minDate = new Date(min);
  maxDate = new Date(max);
  totalDays = Math.ceil((max - min) / 86400000);
}}

function scalePx() {{ return {{D:40,W:10,M:2.5,Q:1}}[currentScale] || 10; }}

function dateToX(dateStr) {{
  if (!dateStr) return null;
  return Math.round((+new Date(dateStr) - +minDate) / 86400000 * pxPerDay);
}}

function render() {{
  pxPerDay = scalePx();
  const totalW = Math.ceil(totalDays * pxPerDay);
  const includeText = document.getElementById('filter-include').value.trim().toLowerCase();
  const excludeText = document.getElementById('filter-exclude').value.trim().toLowerCase();

  visibleRows = ROWS.filter(r => {{
    if (isAncestorCollapsed(r)) return false;
    const ryg = ['Green','Yellow','Red'].includes(r.ryg) ? r.ryg : 'Gray';
    if (!visibleRYG.has(ryg)) return false;
    const name = (r.name || '').toLowerCase();
    if (includeText && !name.includes(includeText)) return false;
    if (excludeText && name.includes(excludeText)) return false;
    return true;
  }});

  renderLabels();
  renderAxis(totalW);
  renderBars(totalW);
}}

function rygColor(row) {{
  if (row.statusEmoji === '✅') return RYG_DONE;
  return RYG_COLORS[row.ryg] || RYG_COLORS['Gray'];
}}

function renderLabels() {{
  const container = document.getElementById('label-rows');
  container.innerHTML = '';
  visibleRows.forEach(r => {{
    const depth = getDepth(r);
    const hasCh = hasChildren(r.id);
    const isGroup = !!r.statusEmoji;

    const div = document.createElement('div');
    div.className = 'row-label' + (isGroup ? ' group-row' : '') + (r.id === selectedId ? ' selected' : '');
    div.dataset.id = r.id;
    div.style.paddingLeft = (depth * 14 + 4) + 'px';

    const chevron = document.createElement('span');
    chevron.className = 'chevron';
    chevron.textContent = hasCh ? (collapsed.has(r.id) ? '▶' : '▼') : '';
    if (hasCh) chevron.onclick = e => {{ e.stopPropagation(); toggleCollapse(r.id); }};

    const circle = document.createElement('span');
    circle.className = 'ryg-circle';
    circle.style.background = rygColor(r);
    if (!r.ryg && !r.statusEmoji) circle.style.opacity = '0';

    const name = document.createElement('span');
    name.className = 'name';
    name.textContent = (r.statusEmoji ? r.statusEmoji + ' ' : '') + (r.name || '—');

    div.appendChild(chevron);
    div.appendChild(circle);
    div.appendChild(name);
    div.addEventListener('click', () => selectRow(r));
    div.addEventListener('mouseenter', e => showTooltip(e, r));
    div.addEventListener('mouseleave', hideTooltip);
    div.addEventListener('mousemove', moveTooltip);
    container.appendChild(div);
  }});
}}

function renderAxis(totalW) {{
  const axis = document.getElementById('time-axis');
  axis.innerHTML = '';
  const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('width', totalW);
  svg.setAttribute('height', AXIS_H);

  const cur = new Date(minDate);
  while (cur <= maxDate) {{
    const x = dateToX(cur.toISOString().split('T')[0]);
    let label = '', major = false;

    if (currentScale === 'D') {{
      label = cur.getDate(); major = cur.getDate() === 1;
    }} else if (currentScale === 'W') {{
      if (cur.getDay() === 1) {{ label = cur.toLocaleDateString('en-US',{{month:'short',day:'numeric'}}); major = cur.getDate() <= 7; }}
    }} else if (currentScale === 'M') {{
      if (cur.getDate() === 1) {{ label = cur.toLocaleDateString('en-US',{{month:'short',year:'2-digit'}}); major = cur.getMonth() === 0; }}
    }} else if (currentScale === 'Q') {{
      if (cur.getDate() === 1 && cur.getMonth() % 3 === 0) {{ label = 'Q'+(Math.floor(cur.getMonth()/3)+1)+' '+cur.getFullYear(); major = true; }}
    }}

    if (label) {{
      const line = document.createElementNS('http://www.w3.org/2000/svg','line');
      line.setAttribute('x1',x); line.setAttribute('x2',x);
      line.setAttribute('y1', major ? 0 : 18); line.setAttribute('y2', AXIS_H);
      line.setAttribute('stroke', major ? '#3a3a52' : '#2a2a38'); line.setAttribute('stroke-width','1');
      svg.appendChild(line);
      const text = document.createElementNS('http://www.w3.org/2000/svg','text');
      text.setAttribute('x', x+3); text.setAttribute('y', 14);
      text.setAttribute('fill', major ? '#9090a8' : '#5a5a72');
      text.setAttribute('font-size', major ? '11' : '10');
      text.setAttribute('font-family','Roboto Mono,monospace');
      text.textContent = label;
      svg.appendChild(text);
    }}
    cur.setDate(cur.getDate()+1);
  }}

  const todayX = dateToX(new Date().toISOString().split('T')[0]);
  if (todayX >= 0 && todayX <= totalW) {{
    const line = document.createElementNS('http://www.w3.org/2000/svg','line');
    line.setAttribute('x1',todayX); line.setAttribute('x2',todayX);
    line.setAttribute('y1',0); line.setAttribute('y2',AXIS_H);
    line.setAttribute('stroke','rgb(85,53,243)'); line.setAttribute('stroke-width','2');
    svg.appendChild(line);
  }}

  axis.appendChild(svg);
  axis.style.width = totalW + 'px';
}}

function renderBars(totalW) {{
  const svg = document.getElementById('bars-svg');
  svg.innerHTML = '';
  const totalH = visibleRows.length * ROW_H;
  svg.setAttribute('width', totalW); svg.setAttribute('height', totalH);
  svg.style.width = totalW + 'px'; svg.style.height = totalH + 'px';

  const todayX = dateToX(new Date().toISOString().split('T')[0]);

  visibleRows.forEach((r, i) => {{
    const y = i * ROW_H;

    const bg = document.createElementNS('http://www.w3.org/2000/svg','rect');
    bg.setAttribute('x',0); bg.setAttribute('y',y);
    bg.setAttribute('width',totalW); bg.setAttribute('height',ROW_H);
    bg.setAttribute('fill', i%2===0 ? 'transparent' : 'rgba(255,255,255,0.02)');
    svg.appendChild(bg);

    const hline = document.createElementNS('http://www.w3.org/2000/svg','line');
    hline.setAttribute('x1',0); hline.setAttribute('x2',totalW);
    hline.setAttribute('y1',y+ROW_H-1); hline.setAttribute('y2',y+ROW_H-1);
    hline.setAttribute('stroke','var(--border)'); hline.setAttribute('stroke-width','0.5');
    svg.appendChild(hline);

    if (r.start && r.finish) {{
      const x1 = dateToX(r.start);
      let x2 = dateToX(r.finish);
      if (x2 <= x1) x2 = x1 + Math.max(2, pxPerDay);
      const barH = r.statusEmoji ? 10 : 8;
      const barY = y + (ROW_H - barH) / 2;

      const bar = document.createElementNS('http://www.w3.org/2000/svg','rect');
      bar.setAttribute('x',x1); bar.setAttribute('y',barY);
      bar.setAttribute('width',x2-x1); bar.setAttribute('height',barH);
      bar.setAttribute('rx','2'); bar.setAttribute('fill', rygColor(r));
      bar.setAttribute('opacity', r.statusEmoji ? '0.9' : '0.7');
      svg.appendChild(bar);

      const pct = parseFloat(r.pctComplete) || 0;
      if (pct > 0) {{
        const fill = document.createElementNS('http://www.w3.org/2000/svg','rect');
        fill.setAttribute('x',x1); fill.setAttribute('y',barY);
        fill.setAttribute('width', Math.round((x2-x1)*pct/100)); fill.setAttribute('height',barH);
        fill.setAttribute('rx','2'); fill.setAttribute('fill','rgba(255,255,255,0.3)');
        svg.appendChild(fill);
      }}
    }}

    if (todayX >= 0 && todayX <= totalW) {{
      const tl = document.createElementNS('http://www.w3.org/2000/svg','line');
      tl.setAttribute('x1',todayX); tl.setAttribute('x2',todayX);
      tl.setAttribute('y1',y); tl.setAttribute('y2',y+ROW_H);
      tl.setAttribute('stroke','rgba(85,53,243,0.4)'); tl.setAttribute('stroke-width','1');
      svg.appendChild(tl);
    }}
  }});

  document.getElementById('bars-inner').style.width = totalW + 'px';
}}

function toggleCollapse(id) {{
  if (collapsed.has(id)) collapsed.delete(id); else collapsed.add(id);
  render(); syncScroll();
}}
function collapseAll() {{ ROWS.forEach(r => {{ if (hasChildren(r.id)) collapsed.add(r.id); }}); render(); }}
function expandAll() {{ collapsed.clear(); render(); }}
function changeLevel(delta) {{
  let maxD = Math.max(...visibleRows.map(r => getDepth(r)));
  if (delta > 0) ROWS.forEach(r => {{ if (getDepth(r) === maxD) collapsed.delete(r.id); }});
  else {{ let t = Math.max(0, maxD-1); ROWS.forEach(r => {{ if (getDepth(r) === t && hasChildren(r.id)) collapsed.add(r.id); }}); }}
  render();
}}
function toggleRYG(btn) {{
  btn.classList.toggle('active');
  const ryg = btn.dataset.ryg;
  if (visibleRYG.has(ryg)) visibleRYG.delete(ryg); else visibleRYG.add(ryg);
  applyFilters();
}}
function applyFilters() {{ render(); syncScroll(); }}
function setScale(btn) {{
  document.querySelectorAll('[data-scale]').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentScale = btn.dataset.scale;
  render();
}}
function updateThemeBtn() {{
  const isDark = document.documentElement.dataset.theme === 'dark';
  document.getElementById('theme-btn').innerHTML = isDark
    ? `<svg width="14" height="14" viewBox="0 0 14 14"><circle cx="7" cy="7" r="6" fill="white" stroke="#555" stroke-width="1"/><circle cx="7" cy="7" r="3" fill="black"/></svg>`
    : `<svg width="14" height="14" viewBox="0 0 14 14"><circle cx="7" cy="7" r="6" fill="white" stroke="#aaa" stroke-width="1"/></svg>`;
}}
function toggleTheme() {{
  const html = document.documentElement;
  const next = html.dataset.theme === 'dark' ? 'light' : 'dark';
  html.dataset.theme = next;
  localStorage.setItem('tl-theme', next);
  updateThemeBtn();
}}

let ttTarget = null;
function showTooltip(e, row) {{
  ttTarget = row;
  const tt = document.getElementById('tooltip');
  let html = `<div class="tt-name">${{row.name || '—'}}</div>`;
  if (row.ryg || row.statusEmoji) html += `<div class="tt-row"><span class="tt-label">Status</span><span>${{row.statusEmoji||''}} ${{row.ryg||''}}</span></div>`;
  if (row.start) html += `<div class="tt-row"><span class="tt-label">Start</span><span>${{row.start}}</span></div>`;
  if (row.finish) html += `<div class="tt-row"><span class="tt-label">Finish</span><span>${{row.finish}}</span></div>`;
  if (row.duration) html += `<div class="tt-row"><span class="tt-label">Duration</span><span>${{row.duration}}</span></div>`;
  if (row.assignee) html += `<div class="tt-row"><span class="tt-label">Assignee</span><span>${{row.assignee}}</span></div>`;
  tt.innerHTML = html;
  tt.style.display = 'block';
  moveTooltip(e);
}}
function moveTooltip(e) {{ positionTooltip(e); }}
function hideTooltip() {{ document.getElementById('tooltip').style.display='none'; ttTarget=null; }}

function selectRow(row) {{
  selectedId = row.id; render();
  const fields = [
    ['Name',row.name],['Status',(row.statusEmoji||'')+' '+(row.ryg||'')],
    ['Start',row.start],['Finish',row.finish],['Duration',row.duration],
    ['Assignee',row.assignee],['% Complete',row.pctComplete?row.pctComplete+'%':null],
    ['Predecessors',row.predecessors],['Comments',row.comments],
    ['Master Schedule',row.masterScheduleItem?'Yes':null],
  ];
  let html = `<h2>${{(row.statusEmoji?row.statusEmoji+' ':'')+( row.name||'')}}</h2>`;
  fields.forEach(([label,val]) => {{
    if (!val || !String(val).trim()) return;
    html += `<div class="detail-field"><div class="detail-label">${{label}}</div><div class="detail-value">${{val}}</div></div>`;
  }});
  const children = ROWS.filter(r => r.parentId === row.id);
  if (children.length) html += `<div class="detail-field"><div class="detail-label">Sub-tasks</div><div class="detail-value">${{children.length}}</div></div>`;
  document.getElementById('detail-content').innerHTML = html;
  document.getElementById('detail-panel').classList.add('open');
}}
function closeDetail() {{
  document.getElementById('detail-panel').classList.remove('open');
  selectedId = null; render();
}}

function setupSync() {{
  const lp = document.getElementById('label-panel');
  const bw = document.getElementById('bars-wrap');
  let syncing = false;
  lp.addEventListener('scroll', () => {{ if (syncing) return; syncing=true; bw.scrollTop=lp.scrollTop; syncing=false; }});
  bw.addEventListener('scroll', () => {{ if (syncing) return; syncing=true; lp.scrollTop=bw.scrollTop; syncing=false; }});
}}
function syncScroll() {{
  const lp = document.getElementById('label-panel');
  document.getElementById('bars-wrap').scrollTop = lp.scrollTop;
}}
function setupResize() {{
  const handle = document.getElementById('resize-handle');
  const lp = document.getElementById('label-panel');
  let dragging=false, startX=0, startW=0;
  handle.addEventListener('mousedown', e => {{ dragging=true; startX=e.clientX; startW=lp.offsetWidth; document.body.style.cursor='col-resize'; e.preventDefault(); }});
  document.addEventListener('mousemove', e => {{ if (!dragging) return; lp.style.width=Math.min(500,Math.max(200,startW+e.clientX-startX))+'px'; }});
  document.addEventListener('mouseup', () => {{ dragging=false; document.body.style.cursor=''; }});
}}

const savedTheme = localStorage.getItem('tl-theme');
if (savedTheme) document.documentElement.dataset.theme = savedTheme;
updateThemeBtn();
init();
</script>
</body>
</html>"""


def main():
    print("Fetching Smartsheet data...")
    rows = fetch_rows()
    print(f"  {{len(rows)}} rows fetched")

    updated_at = datetime.now(timezone.utc).isoformat()
    html = build_html(rows, updated_at)

    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = os.path.join(tmpdir, "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print("Deploying via wrangler...")
        env = {{**os.environ,
               "CLOUDFLARE_API_TOKEN": CF_API_TOKEN,
               "CLOUDFLARE_ACCOUNT_ID": CF_ACCOUNT_ID}}
        result = subprocess.run(
            ["wrangler", "pages", "deploy", tmpdir,
             "--project-name", CF_PROJECT_NAME, "--branch", "main"],
            capture_output=True, text=True, env=env
        )
        print(result.stdout)
        if result.returncode != 0:
            print("ERROR:", result.stderr)
            exit(1)


if __name__ == "__main__":
    main()
