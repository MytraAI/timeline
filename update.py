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
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
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

html,body{{height:100%;background:var(--bg);color:var(--text);font-family:'JetBrains Mono',monospace;font-size:12px;overflow:hidden}}

/* ── Toolbar ── */
#toolbar{{display:flex;align-items:center;gap:8px;padding:6px 12px;background:var(--bg2);border-bottom:1px solid var(--border);flex-shrink:0;flex-wrap:wrap}}
#toolbar h1{{font-family:'Barlow Condensed',sans-serif;font-size:18px;font-weight:700;letter-spacing:1px;color:var(--text);margin-right:8px}}
.tb-sep{{width:1px;height:20px;background:var(--border);margin:0 4px}}
.btn{{background:var(--bg3);border:1px solid var(--border);color:var(--text2);padding:3px 8px;border-radius:4px;cursor:pointer;font-size:11px;font-family:'JetBrains Mono',monospace;transition:all .15s}}
.btn:hover{{border-color:var(--accent);color:var(--text)}}
.btn.active{{background:var(--accent-light);border-color:var(--accent);color:var(--accent)}}
.ryg-btn{{display:flex;align-items:center;gap:4px;padding:3px 7px}}
.ryg-dot{{width:8px;height:8px;border-radius:50%;display:inline-block;flex-shrink:0}}
#filter-include,#filter-exclude{{background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:3px 7px;border-radius:4px;font-size:11px;font-family:'JetBrains Mono',monospace;width:120px}}
#filter-include::placeholder,#filter-exclude::placeholder{{color:var(--text3)}}
#updated{{margin-left:auto;color:var(--text3);font-size:10px;white-space:nowrap}}

/* ── Main layout ── */
#app{{display:flex;flex-direction:column;height:100vh}}
#gantt-wrap{{display:flex;flex:1;overflow:hidden;position:relative}}

/* ── Left label panel ── */
#label-panel{{width:320px;min-width:200px;max-width:500px;flex-shrink:0;overflow-y:auto;overflow-x:hidden;border-right:1px solid var(--border);background:var(--bg2);position:relative}}
#label-header{{height:36px;display:flex;align-items:center;padding:0 8px;border-bottom:1px solid var(--border);background:var(--bg2);position:sticky;top:0;z-index:2;font-family:'Barlow Condensed',sans-serif;font-size:13px;font-weight:600;color:var(--text2);letter-spacing:.5px}}

.row-label{{display:flex;align-items:center;height:28px;padding-right:8px;cursor:pointer;border-bottom:1px solid var(--border);transition:background .1s;position:relative}}
.row-label:hover{{background:var(--bg3)}}
.row-label.selected{{background:var(--accent-light)}}
.row-label .indent{{flex-shrink:0}}
.row-label .chevron{{width:16px;flex-shrink:0;color:var(--text3);font-size:10px;text-align:center;user-select:none}}
.row-label .ryg-circle{{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-right:5px}}
.row-label .name{{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--text);font-size:11px}}
.row-label.group-row .name{{font-family:'Barlow Condensed',sans-serif;font-size:13px;font-weight:600;letter-spacing:.3px}}
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
#tooltip .tt-name{{font-family:'Barlow Condensed',sans-serif;font-size:14px;font-weight:600;color:var(--text);margin-bottom:5px;line-height:1.2}}
#tooltip .tt-row{{display:flex;gap:6px;color:var(--text2);margin-top:2px}}
#tooltip .tt-label{{color:var(--text3);min-width:55px}}

/* ── Detail panel ── */
#detail-panel{{position:fixed;right:0;top:0;bottom:0;width:360px;background:var(--panel-bg);border-left:1px solid var(--border);z-index:50;transform:translateX(100%);transition:transform .25s ease;overflow-y:auto;padding:16px}}
#detail-panel.open{{transform:translateX(0)}}
#detail-close{{float:right;background:none;border:none;color:var(--text2);cursor:pointer;font-size:16px;padding:0 4px}}
#detail-panel h2{{font-family:'Barlow Condensed',sans-serif;font-size:18px;font-weight:700;color:var(--text);margin-bottom:12px;padding-right:24px;line-height:1.2}}
.detail-field{{margin-bottom:8px}}
.detail-label{{color:var(--text3);font-size:10px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px}}
.detail-value{{color:var(--text);font-size:12px;word-break:break-word}}

/* ── Resize handle ── */
#resize-handle{{width:4px;cursor:col-resize;background:transparent;flex-shrink:0;transition:background .15s}}
#resize-handle:hover{{background:var(--accent)}}
</style>
</head>
<body>
<div id="app">
  <div id="toolbar">
    <h1>TIMELINE</h1>
    <div class="tb-sep"></div>
    <button class="btn" onclick="collapseAll()">Collapse All</button>
    <button class="btn" onclick="expandAll()">Expand All</button>
    <button class="btn" onclick="changeLevel(-1)">− Level</button>
    <button class="btn" onclick="changeLevel(1)">+ Level</button>
    <div class="tb-sep"></div>
    <button class="btn ryg-btn active" data-ryg="Green" onclick="toggleRYG(this)"><span class="ryg-dot" style="background:var(--ryg-green)"></span>Green</button>
    <button class="btn ryg-btn active" data-ryg="Yellow" onclick="toggleRYG(this)"><span class="ryg-dot" style="background:var(--ryg-yellow)"></span>Yellow</button>
    <button class="btn ryg-btn active" data-ryg="Red" onclick="toggleRYG(this)"><span class="ryg-dot" style="background:var(--ryg-red)"></span>Red</button>
    <button class="btn ryg-btn active" data-ryg="Gray" onclick="toggleRYG(this)"><span class="ryg-dot" style="background:var(--ryg-gray)"></span>Gray</button>
    <button class="btn ryg-btn active" data-ryg="null" onclick="toggleRYG(this)"><span class="ryg-dot" style="background:var(--border)"></span>None</button>
    <div class="tb-sep"></div>
    <input id="filter-include" placeholder="include..." oninput="applyFilters()">
    <input id="filter-exclude" placeholder="exclude..." oninput="applyFilters()">
    <div class="tb-sep"></div>
    <button class="btn active" data-scale="W" onclick="setScale(this)">Week</button>
    <button class="btn" data-scale="D" onclick="setScale(this)">Day</button>
    <button class="btn" data-scale="M" onclick="setScale(this)">Month</button>
    <button class="btn" data-scale="Q" onclick="setScale(this)">Quarter</button>
    <div class="tb-sep"></div>
    <button class="btn" onclick="toggleTheme()">🌓</button>
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
const RYG_COLORS = {{Green:'#22c55e',Yellow:'#eab308',Red:'#ef4444',Gray:'#6b7280',null:'#3a3a4a'}};
const RYG_DONE = '#5535f3';
const ACCENT = 'rgb(85,53,243)';

// ── State ──
let collapsed = new Set();
let visibleRYG = new Set(['Green','Yellow','Red','Gray','null']);
let currentScale = 'W';
let selectedId = null;
let rowMap = {{}};
let visibleRows = [];
let minDate, maxDate, totalDays, pxPerDay;

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

function scalePx() {{
  return {{D:40, W:10, M:2.5, Q:1}}[currentScale] || 10;
}}

function dateToX(dateStr) {{
  if (!dateStr) return null;
  const ms = +new Date(dateStr) - +minDate;
  return Math.round(ms / 86400000 * pxPerDay);
}}

// ── Render ──
function render() {{
  pxPerDay = scalePx();
  const totalW = Math.ceil(totalDays * pxPerDay);

  // Compute visible rows
  const includeText = document.getElementById('filter-include').value.trim().toLowerCase();
  const excludeText = document.getElementById('filter-exclude').value.trim().toLowerCase();

  visibleRows = ROWS.filter(r => {{
    if (isAncestorCollapsed(r)) return false;
    const ryg = r.ryg ? r.ryg : 'null';
    if (!visibleRYG.has(ryg) && !visibleRYG.has(r.ryg)) {{
      // Check if ryg matches any active filter
      if (!visibleRYG.has(ryg)) return false;
    }}
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
  const end = new Date(maxDate);

  while (cur <= end) {{
    const x = dateToX(cur.toISOString().split('T')[0]);
    let label = '';
    let major = false;

    if (currentScale === 'D') {{
      label = cur.getDate();
      major = cur.getDate() === 1;
    }} else if (currentScale === 'W') {{
      const day = cur.getDay();
      if (day === 1) {{
        label = cur.toLocaleDateString('en-US',{{month:'short',day:'numeric'}});
        major = cur.getDate() <= 7;
      }}
    }} else if (currentScale === 'M') {{
      if (cur.getDate() === 1) {{
        label = cur.toLocaleDateString('en-US',{{month:'short',year:'2-digit'}});
        major = cur.getMonth() === 0;
      }}
    }} else if (currentScale === 'Q') {{
      if (cur.getDate() === 1 && cur.getMonth() % 3 === 0) {{
        const q = Math.floor(cur.getMonth()/3)+1;
        label = 'Q'+q+' '+cur.getFullYear();
        major = true;
      }}
    }}

    if (label) {{
      const line = document.createElementNS('http://www.w3.org/2000/svg','line');
      line.setAttribute('x1',x); line.setAttribute('x2',x);
      line.setAttribute('y1', major ? 0 : 18);
      line.setAttribute('y2', AXIS_H);
      line.setAttribute('stroke', major ? '#3a3a52' : '#2a2a38');
      line.setAttribute('stroke-width','1');
      svg.appendChild(line);

      const text = document.createElementNS('http://www.w3.org/2000/svg','text');
      text.setAttribute('x', x+3);
      text.setAttribute('y', 14);
      text.setAttribute('fill', major ? '#9090a8' : '#5a5a72');
      text.setAttribute('font-size', major ? '11' : '10');
      text.setAttribute('font-family','JetBrains Mono,monospace');
      text.textContent = label;
      svg.appendChild(text);
    }}

    // advance
    if (currentScale === 'D') cur.setDate(cur.getDate()+1);
    else if (currentScale === 'W') cur.setDate(cur.getDate()+1);
    else if (currentScale === 'M') cur.setDate(cur.getDate()+1);
    else cur.setDate(cur.getDate()+1);
  }}

  // Today line
  const todayX = dateToX(new Date().toISOString().split('T')[0]);
  if (todayX >= 0 && todayX <= totalW) {{
    const line = document.createElementNS('http://www.w3.org/2000/svg','line');
    line.setAttribute('x1',todayX); line.setAttribute('x2',todayX);
    line.setAttribute('y1',0); line.setAttribute('y2',AXIS_H);
    line.setAttribute('stroke','rgb(85,53,243)');
    line.setAttribute('stroke-width','2');
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
  currentScale = btn.dataset.scale;
  render();
}}

// ── Theme ──
function toggleTheme() {{
  const html = document.documentElement;
  const next = html.dataset.theme === 'dark' ? 'light' : 'dark';
  html.dataset.theme = next;
  localStorage.setItem('tl-theme', next);
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

// ── Detail panel ──
function selectRow(row) {{
  selectedId = row.id;
  render();
  const panel = document.getElementById('detail-panel');
  const content = document.getElementById('detail-content');

  const fields = [
    ['Name', row.name],
    ['Status', (row.statusEmoji||'') + ' ' + (row.ryg||'')],
    ['Start', row.start],
    ['Finish', row.finish],
    ['Duration', row.duration],
    ['Assignee', row.assignee],
    ['% Complete', row.pctComplete ? row.pctComplete + '%' : null],
    ['Predecessors', row.predecessors],
    ['Comments', row.comments],
    ['Master Schedule', row.masterScheduleItem ? 'Yes' : null],
  ];

  let html = `<h2>${{row.statusEmoji ? row.statusEmoji + ' ' : ''}}</h2>`;
  html = `<h2>${{(row.statusEmoji ? row.statusEmoji + ' ' : '') + (row.name || '')}}</h2>`;

  fields.forEach(([label, val]) => {{
    if (!val || !String(val).trim()) return;
    html += `<div class="detail-field">
      <div class="detail-label">${{label}}</div>
      <div class="detail-value">${{val}}</div>
    </div>`;
  }});

  // Children count
  const children = ROWS.filter(r => r.parentId === row.id);
  if (children.length) {{
    html += `<div class="detail-field"><div class="detail-label">Sub-tasks</div><div class="detail-value">${{children.length}}</div></div>`;
  }}

  content.innerHTML = html;
  panel.classList.add('open');
}}

function closeDetail() {{
  document.getElementById('detail-panel').classList.remove('open');
  selectedId = null;
  render();
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

init();
</script>
</body>
</html>"""

def main():
    print("Fetching Smartsheet data...")
    rows = fetch_rows()
    print(f"  {len(rows)} rows fetched")

    updated_at = datetime.now(timezone.utc).isoformat()
    html = build_html(rows, updated_at)

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
