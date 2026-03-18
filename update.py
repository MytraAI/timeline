import os, json, requests, subprocess, tempfile, argparse
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
        if not node.get("name") or not str(node["name"]).strip():
            continue
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

/* ── Toolbar ── */
#toolbar{{display:flex;align-items:center;gap:8px;padding:6px 12px;background:var(--bg2);border-bottom:1px solid var(--border);flex-shrink:0;flex-wrap:wrap}}
#toolbar-logo{{height:28px;display:block;filter:invert(1);margin-right:8px}}
:root[data-theme="light"] #toolbar-logo{{filter:invert(0)}}
.tb-sep{{width:1px;height:20px;background:var(--border);margin:0 4px}}
.btn{{background:var(--bg3);border:1px solid var(--border);color:var(--text2);padding:3px 8px;border-radius:4px;cursor:pointer;font-size:11px;font-family:'Roboto Mono',monospace;transition:all .15s}}
.btn:hover{{border-color:var(--accent);color:var(--text)}}
.btn.active{{background:var(--accent-light);border-color:var(--accent);color:var(--accent)}}
.ryg-btn{{width:20px;height:20px;border-radius:50%;border:2px solid transparent;padding:0;flex-shrink:0;transition:transform .15s,border-color .15s,opacity .15s}}
.ryg-btn:hover{{transform:scale(1.2);border-color:rgba(255,255,255,0.4) !important}}
.ryg-btn:not(.active){{opacity:0.25}}
.ryg-btn.active{{opacity:1;border-color:rgba(255,255,255,0.2)}}
#filter-include,#filter-exclude{{background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:3px 7px;border-radius:4px;font-size:11px;font-family:'Roboto Mono',monospace;width:120px}}
#filter-include::placeholder,#filter-exclude::placeholder{{color:var(--text3)}}
#updated{{margin-left:auto;color:var(--text3);font-size:10px;white-space:nowrap}}

/* ── Main layout ── */
#app{{display:flex;flex-direction:column;height:100vh}}
#gantt-wrap{{display:flex;flex:1;overflow:hidden;position:relative}}

/* ── Left label panel ── */
#label-panel{{width:320px;min-width:200px;max-width:500px;flex-shrink:0;overflow-y:auto;overflow-x:hidden;border-right:1px solid var(--border);background:var(--bg2);position:relative}}
#label-header{{height:36px;display:flex;align-items:center;padding:0 8px;border-bottom:1px solid var(--border);background:var(--bg2);position:sticky;top:0;z-index:2;font-family:'Roboto',sans-serif;font-size:13px;font-weight:600;color:var(--text2);letter-spacing:.5px}}

.row-label{{display:flex;align-items:center;height:28px;padding-right:8px;cursor:pointer;border-bottom:1px solid var(--border);transition:background .1s;position:relative}}
.row-label:hover{{background:var(--bg3)}}
.row-label.selected{{background:var(--accent-light)}}
.row-label .indent{{flex-shrink:0}}
.row-label .chevron{{width:16px;flex-shrink:0;color:var(--text3);font-size:10px;text-align:center;user-select:none}}
.row-label .ryg-circle{{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-right:5px}}
.row-label .name{{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--text);font-size:11px}}
.row-label.group-row .name{{font-family:'Roboto',sans-serif;font-size:13px;font-weight:600;letter-spacing:.3px}}
.row-label.hidden{{display:none}}

/* ── Right bars panel ── */
#bars-wrap{{flex:1;overflow:auto;position:relative}}
#bars-inner{{position:relative}}
#time-axis{{height:36px;position:sticky;top:0;z-index:3;background:var(--bg2);border-bottom:1px solid var(--border)}}
#bars-svg{{display:block}}

/* ── Scrollbar sync ── */
#label-panel::-webkit-scrollbar,#bars-wrap::-webkit-scrollbar{{width:6px;height:6px}}
#label-panel::-webkit-scrollbar-track,#bars-wrap::-webkit-scrollbar-track{{background:var(--bg)}}
#label-panel::-webkit-scrollbar-thumb,#bars-wrap::-webkit-scrollbar-thumb{{background:var(--border);border-radius:3px}}

/* ── Tooltip ── */
#tooltip{{position:fixed;pointer-events:none;background:var(--tooltip-bg);border:1px solid var(--border);border-radius:6px;padding:8px 10px;font-size:11px;z-index:100;display:none;max-width:240px;box-shadow:0 4px 16px rgba(0,0,0,0.4)}}
#tooltip .tt-name{{font-family:'Roboto',sans-serif;font-size:14px;font-weight:600;color:var(--text);margin-bottom:5px;line-height:1.2}}
#tooltip .tt-row{{display:flex;gap:6px;color:var(--text2);margin-top:2px}}
#tooltip .tt-label{{color:var(--text3);min-width:55px}}


/* ── Resize handle ── */
#resize-handle{{width:4px;cursor:col-resize;background:transparent;flex-shrink:0;transition:background .15s}}
#resize-handle:hover{{background:var(--accent)}}
</style>
</head>
<body>
<div id="app">
  <div id="toolbar">
    <img id="toolbar-logo" src="data:image/svg+xml;base64,{LOGO_B64}" alt="Mytra">
    <div class="tb-sep"></div>
    <button class="btn" onclick="collapseAll()">− all</button>
    <button class="btn" onclick="changeLevel(-1)">−</button>
    <button class="btn" onclick="changeLevel(1)">+</button>
    <button class="btn" onclick="expandAll()">+ all</button>
    <div class="tb-sep"></div>
    <button class="ryg-btn active" data-ryg="Green" onclick="toggleRYG(this)" style="background:var(--ryg-green)"></button>
    <button class="ryg-btn active" data-ryg="Yellow" onclick="toggleRYG(this)" style="background:var(--ryg-yellow)"></button>
    <button class="ryg-btn active" data-ryg="Red" onclick="toggleRYG(this)" style="background:var(--ryg-red)"></button>
    <button class="ryg-btn active" data-ryg="Gray" onclick="toggleRYG(this)" style="background:var(--ryg-gray)"></button>
    <div class="tb-sep"></div>
    <input id="filter-include" placeholder="include..." oninput="applyFilters()">
    <input id="filter-exclude" placeholder="exclude..." oninput="applyFilters()">
    <div class="tb-sep"></div>
    <button class="btn active" data-scale="W" onclick="setScale(this)">Week</button>
    <button class="btn" data-scale="D" onclick="setScale(this)">Day</button>
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

<script>
const __DATA__ = {data_json};
const ROWS = __DATA__.rows;
const ROW_H = 28;
const AXIS_H = 36;
const RYG_COLORS = {{Green:'#22c55e',Yellow:'#eab308',Red:'#ef4444',Gray:'#6b7280',null:'#3a3a4a'}};
const EMOJI_COLORS = {{'🟢':'#22c55e','🟡':'#eab308','🔴':'#ef4444','⚪':'#6b7280','✅':'#5535f3'}};
const RYG_DONE = '#5535f3';
const ACCENT = 'rgb(85,53,243)';

// ── State ──
let collapsed = new Set();
let visibleRYG = new Set(['Green','Yellow','Red','Gray']);
let selectedId = null;
let pxPerDay = 10;
let prevPxPerDay = null;
let rowMap = {{}};
let visibleRows = [];
let minDate, maxDate, totalDays;

// ── Init ──
function init() {{
  // Build rowMap
  ROWS.forEach(r => rowMap[r.id] = r);

  // Set updated timestamp
  const d = new Date(__DATA__.updatedAt);
  document.getElementById('updated').textContent = 'Updated ' + d.toLocaleString();

  // Default collapse: expand root + depth-1 only
  ROWS.forEach(r => {{
    const depth = getDepth(r);
    if (depth >= 2) collapsed.add(r.id);
  }});

  computeDateRange();
  render();
  setupSync();
  setupResize();
  setupZoom();
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

function hasChildren(id) {{
  return ROWS.some(r => r.parentId === id);
}}

function computeDateRange() {{
  let min = Infinity, max = -Infinity;
  ROWS.forEach(r => {{
    if (r.start) {{ const d = +new Date(r.start); if (d < min) min = d; }}
    if (r.finish) {{ const d = +new Date(r.finish); if (d > max) max = d; }}
  }});
  // Pad 2 weeks on each side
  min -= 14 * 86400000;
  max += 14 * 86400000;
  minDate = new Date(min);
  maxDate = new Date(max);
  totalDays = Math.ceil((max - min) / 86400000);
}}

function dateToX(dateStr) {{
  if (!dateStr) return null;
  const ms = +new Date(dateStr) - +minDate;
  return Math.round(ms / 86400000 * pxPerDay);
}}

// ── Render ──
function render() {{
  const totalW = Math.ceil(totalDays * pxPerDay);

  // Compute visible rows
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
  if (row.statusEmoji && EMOJI_COLORS[row.statusEmoji]) return EMOJI_COLORS[row.statusEmoji];
  return RYG_COLORS[row.ryg] || RYG_COLORS['null'];
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
    if (hasCh) {{
      chevron.onclick = e => {{ e.stopPropagation(); toggleCollapse(r.id); }};
    }}

    const name = document.createElement('span');
    name.className = 'name';
    name.textContent = (r.statusEmoji ? r.statusEmoji + ' ' : '') + (r.name || '—');

    div.appendChild(chevron);
    div.appendChild(name);

    div.addEventListener('click', () => selectRow(r));
    div.addEventListener('mouseenter', e => showTooltip(e, r));
    div.addEventListener('mouseleave', hideTooltip);
    div.addEventListener('mousemove', moveTooltip);

    container.appendChild(div);
  }});
}}

function svgLine(svg, x, y1, y2, stroke, sw) {{
  const l = document.createElementNS('http://www.w3.org/2000/svg','line');
  l.setAttribute('x1',x); l.setAttribute('x2',x);
  l.setAttribute('y1',y1); l.setAttribute('y2',y2);
  l.setAttribute('stroke',stroke); l.setAttribute('stroke-width',sw||1);
  svg.appendChild(l);
}}
function svgText(svg, x, y, label, fill, size) {{
  const t = document.createElementNS('http://www.w3.org/2000/svg','text');
  t.setAttribute('x',x); t.setAttribute('y',y);
  t.setAttribute('fill',fill); t.setAttribute('font-size',size||10);
  t.setAttribute('font-family','Roboto Mono,monospace');
  t.textContent = label;
  svg.appendChild(t);
}}

function renderAxis(totalW) {{
  const axis = document.getElementById('time-axis');
  axis.innerHTML = '';
  const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('width', totalW);
  svg.setAttribute('height', AXIS_H);

  // Auto-pick tick granularity from zoom level
  const grain = pxPerDay >= 20 ? 'D' : pxPerDay >= 3 ? 'W' : pxPerDay >= 0.6 ? 'M' : 'Q';

  const cur = new Date(minDate);
  const end = new Date(maxDate);

  if (grain === 'D') {{
    // Two-band: top = month name, bottom = day number
    while (cur <= end) {{
      const x = dateToX(cur.toISOString().split('T')[0]);
      // Day tick + number (bottom band)
      svgLine(svg, x, 18, AXIS_H, '#2a2a38');
      svgText(svg, x+3, 30, cur.getDate(), '#6a6a82', 10);
      // Month boundary (top band)
      if (cur.getDate() === 1) {{
        svgLine(svg, x, 0, AXIS_H, '#3a3a52');
        svgText(svg, x+4, 13, cur.toLocaleDateString('en-US',{{month:'long',year:'numeric'}}), '#9090a8', 11);
      }}
      cur.setDate(cur.getDate()+1);
    }}
    // Pinned month label: if the 1st of the current visible month is off to the left,
    // draw the month name at x=4 so the user always knows which month they're viewing.
    // (rendered last so it paints over day numbers)
    const bw = document.getElementById('bars-wrap');
    const scrollLeft = bw ? bw.scrollLeft : 0;
    const visibleDate = new Date(+minDate + scrollLeft / pxPerDay * 86400000);
    const pinMonth = new Date(visibleDate.getFullYear(), visibleDate.getMonth(), 1);
    const pinX = dateToX(pinMonth.toISOString().split('T')[0]);
    if (pinX < scrollLeft + 4) {{
      // Draw semi-transparent background rect then label
      const bg = document.createElementNS('http://www.w3.org/2000/svg','rect');
      bg.setAttribute('x', scrollLeft); bg.setAttribute('y', 0);
      bg.setAttribute('width', 160); bg.setAttribute('height', 17);
      bg.setAttribute('fill','var(--bg2)');
      svg.appendChild(bg);
      svgText(svg, scrollLeft+4, 13,
        visibleDate.toLocaleDateString('en-US',{{month:'long',year:'numeric'}}),
        '#9090a8', 11);
    }}
  }} else {{
    while (cur <= end) {{
      const x = dateToX(cur.toISOString().split('T')[0]);
      let label = '';
      let major = false;

      if (grain === 'W') {{
        if (cur.getDay() === 1) {{
          label = cur.toLocaleDateString('en-US',{{month:'short',day:'numeric'}});
          major = cur.getDate() <= 7;
        }}
      }} else if (grain === 'M') {{
        if (cur.getDate() === 1) {{
          label = cur.toLocaleDateString('en-US',{{month:'short',year:'2-digit'}});
          major = cur.getMonth() === 0;
        }}
      }} else {{
        if (cur.getDate() === 1 && cur.getMonth() % 3 === 0) {{
          label = 'Q'+(Math.floor(cur.getMonth()/3)+1)+' '+cur.getFullYear();
          major = true;
        }}
      }}

      if (label) {{
        svgLine(svg, x, major ? 0 : 18, AXIS_H, major ? '#3a3a52' : '#2a2a38');
        svgText(svg, x+3, 14, label, major ? '#9090a8' : '#5a5a72', major ? 11 : 10);
      }}
      cur.setDate(cur.getDate()+1);
    }}
  }}

  // Today line
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
  svg.setAttribute('width', totalW);
  svg.setAttribute('height', totalH);
  svg.style.width = totalW + 'px';
  svg.style.height = totalH + 'px';

  // Today line
  const todayX = dateToX(new Date().toISOString().split('T')[0]);

  visibleRows.forEach((r, i) => {{
    const y = i * ROW_H;

    // Row bg alternating
    const bg = document.createElementNS('http://www.w3.org/2000/svg','rect');
    bg.setAttribute('x',0); bg.setAttribute('y',y);
    bg.setAttribute('width',totalW); bg.setAttribute('height',ROW_H);
    bg.setAttribute('fill', i%2===0 ? 'transparent' : 'rgba(255,255,255,0.02)');
    svg.appendChild(bg);

    // Horizontal grid line
    const hline = document.createElementNS('http://www.w3.org/2000/svg','line');
    hline.setAttribute('x1',0); hline.setAttribute('x2',totalW);
    hline.setAttribute('y1',y+ROW_H-1); hline.setAttribute('y2',y+ROW_H-1);
    hline.setAttribute('stroke','var(--border)'); hline.setAttribute('stroke-width','0.5');
    svg.appendChild(hline);

    // Bar
    if (r.start && r.finish) {{
      const x1 = dateToX(r.start);
      let x2 = dateToX(r.finish);
      if (x2 <= x1) x2 = x1 + Math.max(2, pxPerDay);

      const barH = r.statusEmoji ? 10 : 8;
      const barY = y + (ROW_H - barH) / 2;

      // Main bar
      const bar = document.createElementNS('http://www.w3.org/2000/svg','rect');
      bar.setAttribute('x',x1); bar.setAttribute('y',barY);
      bar.setAttribute('width',x2-x1); bar.setAttribute('height',barH);
      bar.setAttribute('rx','2');
      bar.setAttribute('fill', rygColor(r));
      bar.setAttribute('opacity', r.statusEmoji ? '0.9' : '0.7');
      svg.appendChild(bar);

      // % complete fill
      const pct = parseFloat(r.pctComplete) || 0;
      if (pct > 0) {{
        const fillW = Math.round((x2-x1) * pct / 100);
        const fill = document.createElementNS('http://www.w3.org/2000/svg','rect');
        fill.setAttribute('x',x1); fill.setAttribute('y',barY);
        fill.setAttribute('width',fillW); fill.setAttribute('height',barH);
        fill.setAttribute('rx','2');
        fill.setAttribute('fill','rgba(255,255,255,0.3)');
        svg.appendChild(fill);
      }}
    }}

    // Today line per row
    if (todayX >= 0 && todayX <= totalW) {{
      const tl = document.createElementNS('http://www.w3.org/2000/svg','line');
      tl.setAttribute('x1',todayX); tl.setAttribute('x2',todayX);
      tl.setAttribute('y1',y); tl.setAttribute('y2',y+ROW_H);
      tl.setAttribute('stroke','rgba(85,53,243,0.4)'); tl.setAttribute('stroke-width','1');
      svg.appendChild(tl);
    }}

    // Invisible hover overlay — same tooltip as label panel
    const overlay = document.createElementNS('http://www.w3.org/2000/svg','rect');
    overlay.setAttribute('x',0); overlay.setAttribute('y',y);
    overlay.setAttribute('width',totalW); overlay.setAttribute('height',ROW_H);
    overlay.setAttribute('fill','transparent');
    overlay.style.cursor = 'pointer';
    overlay.addEventListener('mouseenter', e => showTooltip(e, r));
    overlay.addEventListener('mouseleave', hideTooltip);
    overlay.addEventListener('mousemove', moveTooltip);
    overlay.addEventListener('click', () => selectRow(r));
    svg.appendChild(overlay);
  }});

  document.getElementById('bars-inner').style.width = totalW + 'px';
}}

// ── Collapse ──
function toggleCollapse(id) {{
  if (collapsed.has(id)) collapsed.delete(id);
  else collapsed.add(id);
  render();
  syncScroll();
}}

function collapseAll() {{
  ROWS.forEach(r => {{ if (hasChildren(r.id)) collapsed.add(r.id); }});
  render();
}}

function expandAll() {{
  collapsed.clear();
  render();
}}

function changeLevel(delta) {{
  // Find current max visible depth
  let depths = visibleRows.map(r => getDepth(r));
  let maxD = Math.max(...depths);
  if (delta > 0) {{
    // expand one more level: remove collapsed for rows at maxD
    ROWS.forEach(r => {{ if (getDepth(r) === maxD) collapsed.delete(r.id); }});
  }} else {{
    // collapse deepest visible parents
    let targetD = maxD - 1;
    if (targetD < 0) targetD = 0;
    ROWS.forEach(r => {{ if (getDepth(r) === targetD && hasChildren(r.id)) collapsed.add(r.id); }});
  }}
  render();
}}

// ── Filters ──
function toggleRYG(btn) {{
  btn.classList.toggle('active');
  const ryg = btn.dataset.ryg;
  if (visibleRYG.has(ryg)) visibleRYG.delete(ryg);
  else visibleRYG.add(ryg);
  applyFilters();
}}

function applyFilters() {{ render(); syncScroll(); }}

// ── Scale ──
function setScale(btn) {{
  document.querySelectorAll('[data-scale]').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  pxPerDay = {{D:40, W:10, M:2.5, Q:0.8}}[btn.dataset.scale] || 10;
  selectedId = null;
  render();
}}

// ── Theme ──
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

// ── Tooltip ──
let ttTarget = null;
function showTooltip(e, row) {{
  ttTarget = row;
  const tt = document.getElementById('tooltip');
  let html = `<div class="tt-name">${{row.name || '—'}}</div>`;
  if (row.ryg || row.statusEmoji) {{
    html += `<div class="tt-row"><span class="tt-label">Status</span><span>${{row.statusEmoji || ''}} ${{row.ryg || ''}}</span></div>`;
  }}
  if (row.start) html += `<div class="tt-row"><span class="tt-label">Start</span><span>${{row.start}}</span></div>`;
  if (row.finish) html += `<div class="tt-row"><span class="tt-label">Finish</span><span>${{row.finish}}</span></div>`;
  if (row.duration) html += `<div class="tt-row"><span class="tt-label">Duration</span><span>${{row.duration}}</span></div>`;
  if (row.assignee) html += `<div class="tt-row"><span class="tt-label">Assignee</span><span>${{row.assignee}}</span></div>`;
  tt.innerHTML = html;
  tt.style.display = 'block';
  moveTooltip(e);
}}

function moveTooltip(e) {{
  const tt = document.getElementById('tooltip');
  const x = e.clientX + 14, y = e.clientY + 10;
  const tw = tt.offsetWidth, th = tt.offsetHeight;
  tt.style.left = (x + tw > window.innerWidth ? x - tw - 20 : x) + 'px';
  tt.style.top = (y + th > window.innerHeight ? y - th - 20 : y) + 'px';
}}

function hideTooltip() {{
  document.getElementById('tooltip').style.display = 'none';
  ttTarget = null;
}}

// ── Row selection ──
const MIN_DAYS = 15;
function selectRow(row) {{
  selectedId = row.id;
  const bw = document.getElementById('bars-wrap');
  if (row.start && row.finish) {{
    const barDays = Math.max(0, (new Date(row.finish) - new Date(row.start)) / 86400000);
    const displayDays = Math.max(barDays, MIN_DAYS);
    pxPerDay = bw.clientWidth / displayDays;
    document.querySelectorAll('[data-scale]').forEach(b => b.classList.remove('active'));
    render();
    const x1 = dateToX(row.start);
    const x2 = dateToX(row.finish);
    if (barDays >= MIN_DAYS) {{
      bw.scrollLeft = Math.max(0, x1);
    }} else {{
      bw.scrollLeft = Math.max(0, (x1 + x2) / 2 - bw.clientWidth / 2);
    }}
  }} else {{
    render();
  }}
}}

// ── Scroll sync ──
function setupSync() {{
  const lp = document.getElementById('label-panel');
  const bw = document.getElementById('bars-wrap');
  let syncing = false;
  lp.addEventListener('scroll', () => {{
    if (syncing) return; syncing = true;
    bw.scrollTop = lp.scrollTop;
    syncing = false;
  }});
  bw.addEventListener('scroll', () => {{
    if (syncing) return; syncing = true;
    lp.scrollTop = bw.scrollTop;
    syncing = false;
  }});
}}

function syncScroll() {{
  const lp = document.getElementById('label-panel');
  const bw = document.getElementById('bars-wrap');
  bw.scrollTop = lp.scrollTop;
}}

// ── Zoom (Ctrl/Cmd + scroll) ──
function setupZoom() {{
  const bw = document.getElementById('bars-wrap');
  bw.addEventListener('wheel', e => {{
    if (!e.ctrlKey && !e.metaKey) return;
    e.preventDefault();
    const rect = bw.getBoundingClientRect();
    const mouseX = e.clientX - rect.left + bw.scrollLeft;
    const factor = e.deltaY < 0 ? 1.18 : 1/1.18;
    const newPx = Math.max(0.2, Math.min(80, pxPerDay * factor));
    const ratio = newPx / pxPerDay;
    pxPerDay = newPx;
    // Clear active scale button since we're freeform
    document.querySelectorAll('[data-scale]').forEach(b => b.classList.remove('active'));
    render();
    bw.scrollLeft = mouseX * ratio - (e.clientX - rect.left);
  }}, {{passive: false}});
}}

// ── Resize handle ──
function setupResize() {{
  const handle = document.getElementById('resize-handle');
  const lp = document.getElementById('label-panel');
  let dragging = false, startX = 0, startW = 0;
  handle.addEventListener('mousedown', e => {{
    dragging = true; startX = e.clientX; startW = lp.offsetWidth;
    document.body.style.cursor = 'col-resize'; e.preventDefault();
  }});
  document.addEventListener('mousemove', e => {{
    if (!dragging) return;
    const w = Math.min(500, Math.max(200, startW + e.clientX - startX));
    lp.style.width = w + 'px';
  }});
  document.addEventListener('mouseup', () => {{
    dragging = false; document.body.style.cursor = '';
  }});
}}

// ── Theme restore ──
const savedTheme = localStorage.getItem('tl-theme');
if (savedTheme) document.documentElement.dataset.theme = savedTheme;
updateThemeBtn();

init();
</script>
</body>
</html>"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skipcloudflare", action="store_true", help="Skip wrangler deployment; write index.html locally")
    args = parser.parse_args()

    print("Fetching Smartsheet data...")
    rows = fetch_rows()
    print(f"  {len(rows)} rows fetched")

    updated_at = datetime.now(timezone.utc).isoformat()
    html = build_html(rows, updated_at)

    if args.skipcloudflare:
        html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Wrote {html_path} (skipped Cloudflare deployment)")
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = os.path.join(tmpdir, "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print("Deploying via wrangler...")
        env = {**os.environ,
               "CLOUDFLARE_API_TOKEN": CF_API_TOKEN,
               "CLOUDFLARE_ACCOUNT_ID": CF_ACCOUNT_ID}
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
