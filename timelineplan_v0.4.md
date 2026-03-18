# TimeLine — Build Plan v0.4

> **Status**: Draft v0.4 — Baseline fields removed. Auth simplified to Cloudflare Zero Trust. VM pipeline retained (no Cloudflare Worker/KV).

---

## What Changed from v0.3

| Item | v0.3 | v0.4 |
|---|---|---|
| Auth | Google OAuth 2.0 via Cloudflare Worker | Cloudflare Zero Trust (email OTP, already live) |
| Data pipeline | Cloudflare Worker + KV + Cron Trigger | Python script on VM + cron job |
| Frontend | React + Vite | Self-contained vanilla JS (single `index.html`) |
| Baseline fields | Included | **Removed** |
| Deployment | wrangler from Worker | wrangler from VM |

---

## Product Overview

TimeLine is an internal web app for Mytra that makes the company's robotics development schedule visible to all employees. The schedule lives in Smartsheet, managed daily by TPMs. TimeLine pulls directly from the Smartsheet API every 6 hours and renders the data as an interactive Gantt chart accessible to all @mytra.ai accounts (via Cloudflare Zero Trust email OTP).

---

## Architecture

```
Smartsheet (TPM daily input)
    ↓ (Smartsheet API v2 — every 6 hours via VM cron job)
Python script on timeline-agent VM
    ↓ (wrangler pages deploy)
mytratimeline.pages.dev (Cloudflare Pages + Zero Trust)
```

### Stack

| Layer | Technology |
|---|---|
| Hosting | Cloudflare Pages |
| Auth | Cloudflare Zero Trust (email OTP, @mytra.ai only) |
| Data source | Smartsheet API v2 |
| Agent | Python 3 on `timeline-agent` VM (cloudy.artym.net) |
| Deployment | wrangler CLI |
| Frontend | Self-contained vanilla JS + SVG (single `index.html`) |

---

## Smartsheet Data

### Sheet
- **Sheet ID:** `3906472049069956`
- **Total rows:** ~1,320
- **Max hierarchy depth:** 6 levels
- **Hierarchy:** via `parentId` field (indent field is null — not used)

### Columns used

| Smartsheet Column | Field in App | Type | Notes |
|---|---|---|---|
| Status | `statusEmoji` | PICKLIST | Emoji: 🟡 🟢 🔴 ✅ ⚪ |
| RYG | `ryg` | PICKLIST | `"Red"`, `"Yellow"`, `"Green"`, `"Gray"`, or null |
| Primary Column | `name` | TEXT_NUMBER | Task / row label |
| Start | `start` | ABSTRACT_DATETIME | Normalize to `YYYY-MM-DD` |
| Finish | `finish` | ABSTRACT_DATETIME | Normalize to `YYYY-MM-DD` |
| Duration | `duration` | DURATION | e.g. `"5d"` |
| Assignee | `assignee` | TEXT_NUMBER | |
| % Complete | `pctComplete` | TEXT_NUMBER | |
| Predecessors | `predecessors` | PREDECESSOR | Display only |
| Comments | `comments` | TEXT_NUMBER | Free text |
| Master Schedule Item | `masterScheduleItem` | CHECKBOX | Boolean |

### Excluded columns
- Baseline Start, Baseline Finish, Baseline Start2, Baseline Finish2
- Variance, Variance2
- Modified, Modified By

---

## Data Pipeline

**File:** `~/timeline-agent/update.py` on `timeline-agent` VM

1. Fetch `GET https://api.smartsheet.com/2.0/sheets/3906472049069956`
2. Build flat row list with fields above (skip Baseline and legacy fields)
3. Preserve `parentId` for tree rendering in the browser
4. Embed as `window.__SCHEDULE__` JSON in generated HTML
5. Deploy via `wrangler pages deploy` to `mytratimeline`

**Cron:** `0 */6 * * *` — already configured on VM

**Secrets** (in `~/cloudy-shared/timeline-agent.env`):
- `SMARTSHEET_API_TOKEN`
- `CF_ACCOUNT_ID`
- `CF_API_TOKEN`

---

## Frontend

Single self-contained `index.html` — no build step, no dependencies except Google Fonts CDN.

### Design

| Property | Value |
|---|---|
| Primary accent | `rgb(85, 53, 243)` |
| Default theme | Dark |
| Aesthetic | Clean, bold, minimal |
| Row padding | Tight — maximize data density |
| RYG circles | 🔴 `#ef4444` / 🟡 `#eab308` / 🟢 `#22c55e` / ⚪ `#6b7280` / ✅ `#5535f3` |
| Gantt bar | Accent purple `rgb(85, 53, 243)`, % complete as lighter fill within bar |
| Font — headers | Barlow Condensed (Google Fonts CDN) |
| Font — data/dates | JetBrains Mono (Google Fonts CDN) |

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│ [CollapseControls] [Filters] [TimeScale] [Theme] [Updated]  │
├───────────────────────────┬─────────────────────────────────┤
│ Task Name (label panel)   │ Timeline (SVG bars panel)       │
│  ● Program                │ ████████████████████            │
│    ● Bobsled              │   ██████████████████████        │
│      ○ P0 Station         │       ██                        │
├───────────────────────────┴─────────────────────────────────┤
│ [Detail Panel — slides in on row click]                     │
└─────────────────────────────────────────────────────────────┘
```

### Components (vanilla JS)

| Component | Description |
|---|---|
| GanttTable | Left label panel — indent tree, RYG circle, row name, collapse chevron |
| GanttBars | Right SVG panel — horizontal bars sized/positioned by Start/Finish |
| TimeAxis | Date header row — Day/Week/Month/Quarter scale |
| HoverTooltip | Compact popup: RYG, Start/Finish, Duration, Assignee |
| DetailPanel | Slide-in side panel on click: all fields, predecessors resolved by name |
| CollapseControls | Expand All / Collapse All / Expand One Level / Collapse One Level |
| FilterBar | RYG status toggles (🟢🟡🔴✅⚪) + text include/exclude search |
| ThemeToggle | Dark / Light — persisted in localStorage |
| RefreshInfo | Last updated timestamp (read-only) |

### Gantt bar rendering
- SVG viewport: spans from `min(start)` to `max(finish)` across all rows
- Bar x position and width computed from date offsets
- `% Complete` shown as lighter fill within bar (`rgba(255,255,255,0.3)`)
- Rows without dates show no bar (label-only)

### Hover behavior
- RYG circle + status emoji
- Start / Finish dates
- Duration
- Assignee

### Click behavior
- Slide-in detail panel (right side)
- Full row details (all fields)
- Predecessors listed by name (resolved from flat row list)
- Comments

### Time scale
- Toggle: **Day / Week / Month / Quarter** (default: Week)
- Controls SVG axis density and tick labels

### Collapse / Expand
- Expand All / Collapse All / Expand One Level / Collapse One Level
- Default: top 2 levels expanded

### Filters
- RYG toggles — show/hide per status (additive)
- Include text search — show only rows whose name matches
- Exclude text search — hide rows whose name matches

---

## Build Order

1. `update.py` — data extraction, tree-ready flat JSON, HTML template scaffold
2. CSS — dark/light theme vars, grid layout, fonts
3. Data parsing — build row map from `window.__SCHEDULE__`
4. GanttTable — label panel with collapse/expand tree
5. GanttBars — SVG bar rendering with date positioning
6. TimeAxis — Week scale (default)
7. HoverTooltip
8. DetailPanel
9. CollapseControls
10. FilterBar (RYG toggles + text search)
11. TimeScaleToggle (Day/Week/Month/Quarter)
12. ThemeToggle
13. End-to-end test with live Smartsheet data

---

## Open Items

1. **TPM email allowlist** — not needed in v0.4 (no admin role, all authenticated users are read-only)
2. **Custom domain** (`timeline.mytra.ai`) — deferred, currently `mytratimeline.pages.dev`

---

*Last updated: 2026-03-18 | Version: 0.4*
