# TimeLine — Build Plan for Claude Code

> **Status**: Draft v0.3 — All critical assumptions resolved. Ready for build.

---

## Product Overview

TimeLine is an internal web app for Mytra that makes the company's robotics development schedule visible to all employees. The schedule lives in Smartsheet, managed daily by TPMs. TimeLine pulls directly from the Smartsheet API every 6 hours, preserving full row hierarchy, and renders the data as an interactive Gantt chart accessible to all @mytra.ai Google accounts.

---

## Architecture

```
Smartsheet (TPM daily input)
    ↓ (Smartsheet API v2 — pulled by Cloudflare Worker every 6 hours)
Cloudflare KV (parsed JSON, keyed as schedule:latest)
    ↓
TimeLine Web App (Cloudflare Pages — served to authenticated users)
```

### Stack

| Layer | Technology |
|---|---|
| Hosting | Cloudflare Pages |
| Serverless functions | Cloudflare Workers |
| Data cache | Cloudflare KV |
| Auth | Google OAuth 2.0, restricted to @mytra.ai domain |
| Data source | Smartsheet API v2 |
| Frontend framework | React (via Vite) |
| Styling | Tailwind CSS |

---

## User Roles

| Role | Access |
|---|---|
| Employee | Read-only schedule view |
| Admin (TPM) | Read-only + manual refresh button |

Role is determined at login by checking if the authenticated Google account is on an allowlist of TPM emails stored as a Cloudflare Worker secret (`ADMIN_EMAILS`, JSON array of strings). No UI for managing this list in v1 — edited manually by the single feature maintainer.

---

## Data Pipeline (The Agent)

### What exists already
- Smartsheet sheet with full schedule, maintained daily by TPMs
- Smartsheet API token
- Smartsheet Sheet ID: `3906472049069956`

### What needs to be built

**Cloudflare Worker: `timeline-agent`**

Responsibilities:
1. Call Smartsheet API v2 `GET /sheets/{sheetId}` with Bearer token
2. Extract all rows with native hierarchy metadata (`parentId`, `indent`) and all required columns
3. Transform flat row list into nested tree structure using `parentId`
4. Store result in Cloudflare KV under key `schedule:latest` with a timestamp
5. Expose `/api/schedule` — returns KV contents to authenticated frontend requests
6. Expose `/api/refresh` — manually triggers steps 1–4, restricted to Admin role only

**Trigger schedule:**
- Cloudflare Cron Trigger: every 6 hours
- Manual trigger: `POST /api/refresh` — callable from the UI by TPMs only

**Smartsheet auth:**
- Bearer token stored as Cloudflare Worker secret: `SMARTSHEET_TOKEN`
- Never hardcoded in source

**Smartsheet API call:**
```
GET https://api.smartsheet.com/2.0/sheets/3906472049069956
Authorization: Bearer {SMARTSHEET_TOKEN}
```

---

## Smartsheet Data Structure

### Column mapping (from actual sheet)

| Smartsheet Column | Field in App | Notes |
|---|---|---|
| `Status` | `statusEmoji` | Emoji: 🟡 🟢 🔴 ✅ ⚪ — indicates hierarchy-level rows |
| `RYG` | `ryg` | Text: `"Red"`, `"Yellow"`, `"Green"`, `"Gray"`, or null |
| `Primary Column` | `name` | Task / row label |
| `Start` | `start` | DateTime from API — normalize to `YYYY-MM-DD` |
| `Finish` | `finish` | DateTime from API — normalize to `YYYY-MM-DD` |
| `Duration` | `duration` | String e.g. `"5d"` |
| `Predecessors` | `predecessors` | String e.g. `"11FS -5d"`, `"446, 474"` — display only in v1 |
| `Variance2` | `variance` | String e.g. `"3d"` or `"0"` |
| `Comments` | `comments` | Free text |
| `Baseline Start` | `baselineStart` | DateTime — normalize to `YYYY-MM-DD` |
| `Baseline Finish` | `baselineFinish` | DateTime — normalize to `YYYY-MM-DD` |
| `Master Schedule Item` | `masterScheduleItem` | Boolean |

### Hierarchy

The Smartsheet API returns rows with native `parentId` and `indent` fields. Use these directly — do not infer hierarchy from the `Status` column.

- Rows **with** a `Status` emoji are section/group headers (Program, subsystem groupings, etc.)
- Rows **without** a `Status` emoji are individual tasks
- `parentId` links child rows to their parent — use this to build the tree

### Status emoji mapping

| Emoji | Meaning |
|---|---|
| 🟢 | On track |
| 🟡 | At risk |
| 🔴 | Off track |
| ✅ | Complete |
| ⚪ | Gray / reference only |

---

## Cloudflare KV Schema

**Key:** `schedule:latest`

```json
{
  "updatedAt": "2026-03-17T14:00:00Z",
  "rows": [
    {
      "id": "row-123456",
      "parentId": null,
      "indent": 0,
      "name": "Program",
      "statusEmoji": "🟡",
      "ryg": "Yellow",
      "start": "2026-03-02",
      "finish": "2026-09-08",
      "duration": "132d",
      "predecessors": null,
      "variance": "0",
      "comments": null,
      "baselineStart": "2026-03-02",
      "baselineFinish": "2026-09-04",
      "masterScheduleItem": true,
      "children": [
        {
          "id": "row-123457",
          "parentId": "row-123456",
          "indent": 1,
          "name": "Bobsled",
          "statusEmoji": "🔴",
          "ryg": "Yellow",
          "start": "2025-12-01",
          "finish": "2027-01-08",
          "duration": "266d",
          "children": []
        }
      ]
    }
  ]
}
```

---

## Authentication

- Google OAuth 2.0
- Domain restriction: `@mytra.ai` only — any other domain rejected at login with a clear error message
- Role check: after domain validation, check authenticated email against TPM allowlist stored in Worker secret `ADMIN_EMAILS` (JSON array of strings)
- Session stored in a signed cookie (Cloudflare Worker generates and validates)
- All `/api/*` routes require a valid session cookie — unauthenticated requests return 401

---

## Frontend

### Primary View: Gantt Chart

- Hierarchical rows, collapsible by level
- Horizontal timeline bars per task, sized and positioned by Start/Finish dates
- RYG status displayed as a filled circle to the left of the task name
- Baseline dates shown as a muted underbar beneath the main Gantt bar when present
- Variance indicator shown on rows where variance > 0
- Comments and predecessor details visible on hover and in click detail panel
- Assignee visible on hover
- Dense layout — minimal row padding to maximize data visible on screen

### Hover Behavior
Hovering a row shows a compact tooltip containing:
- RYG circle + status emoji
- Start / Finish dates
- Duration
- Variance (if non-zero)
- Assignee

### Click Behavior
Clicking a row opens a side panel containing:
- Full row details (all fields)
- Predecessors listed by name (resolved from row IDs)
- Baseline vs actual comparison
- Comments

### Time Scale Controls

Toggle between: **Day / Week / Month / Quarter**
- Default: Week
- Controls the horizontal axis density and bar rendering scale

### Collapse / Expand Controls

Four controls (compact group):
- Expand All
- Collapse All
- Expand One Level
- Collapse One Level

### Filters

- Filter by RYG status (🟢 🟡 🔴 ✅ ⚪) — toggle on/off per status
- Include filter: text search — show only rows whose name matches
- Exclude filter: text search — hide rows whose name matches
- Filters are additive and stackable

### Manual Refresh (Admin only)

- Single button, visible only to TPM/Admin role
- Calls `POST /api/refresh`
- Shows last updated timestamp next to button
- Displays loading state during refresh

### Theme

- Default: Dark mode
- Toggle: Dark / Light
- Preference stored in localStorage

---

## Design Spec

| Property | Value |
|---|---|
| Primary accent | `rgb(85, 53, 243)` |
| Default theme | Dark |
| Theme toggle | Dark / Light |
| Aesthetic | Clean, bold, minimal — as few buttons as possible |
| Row padding | Tight — minimize vertical padding to maximize data density |
| RYG circles | Filled circles: 🔴 `#ef4444` / 🟡 `#eab308` / 🟢 `#22c55e` / ⚪ `#6b7280` / ✅ `#5535f3` |
| Gantt bar | Accent purple `rgb(85, 53, 243)`, % complete shown as lighter fill within bar |
| Baseline bar | Muted gray underbar beneath main bar |
| Font — headers | Characterful, strong sans — e.g. Bebas Neue or Barlow Condensed |
| Font — data/dates | Monospace — e.g. JetBrains Mono or IBM Plex Mono |

---

## Project File Structure

```
timeline/
├── src/
│   ├── app/                        # React frontend (Cloudflare Pages)
│   │   ├── components/
│   │   │   ├── GanttChart.jsx      # Main chart container
│   │   │   ├── GanttRow.jsx        # Single task row + bar
│   │   │   ├── GanttBar.jsx        # Horizontal timeline bar + baseline bar
│   │   │   ├── RYGCircle.jsx       # Status indicator circle
│   │   │   ├── DetailPanel.jsx     # Click-to-open side panel
│   │   │   ├── HoverTooltip.jsx    # Hover tooltip
│   │   │   ├── CollapseControls.jsx
│   │   │   ├── FilterBar.jsx
│   │   │   ├── TimeScaleToggle.jsx
│   │   │   ├── RefreshButton.jsx   # Admin only
│   │   │   └── ThemeToggle.jsx
│   │   ├── hooks/
│   │   │   ├── useSchedule.js      # Fetch + cache schedule data
│   │   │   ├── useCollapse.js      # Collapse/expand state
│   │   │   └── useFilters.js       # Filter state
│   │   ├── context/
│   │   │   ├── AuthContext.jsx
│   │   │   └── ThemeContext.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── worker/                     # Cloudflare Worker (agent + API + auth)
│       ├── index.js                # Router
│       ├── auth.js                 # Google OAuth flow + session management
│       ├── smartsheetClient.js     # Smartsheet API v2 integration
│       ├── rowTransformer.js       # Flat rows → nested tree via parentId
│       └── scheduleStore.js        # Cloudflare KV read/write
├── public/
├── wrangler.toml                   # Cloudflare Pages + Worker + KV + Cron config
├── vite.config.js
└── package.json
```

---

## wrangler.toml Overview

```toml
name = "timeline"
compatibility_date = "2026-01-01"

[[kv_namespaces]]
binding = "SCHEDULE_KV"
id = "<KV_NAMESPACE_ID>"

[triggers]
crons = ["0 */6 * * *"]

[vars]
SMARTSHEET_SHEET_ID = "3906472049069956"
ALLOWED_DOMAIN = "mytra.ai"

# Secrets (set via wrangler CLI, never in code):
# SMARTSHEET_TOKEN
# ADMIN_EMAILS
# SESSION_SECRET
# GOOGLE_OAUTH_CLIENT_ID
# GOOGLE_OAUTH_CLIENT_SECRET
```

---

## Smartsheet API Integration Detail

### Fetching the sheet

```javascript
// smartsheetClient.js
export async function fetchSheet(sheetId, token) {
  const res = await fetch(
    `https://api.smartsheet.com/2.0/sheets/${sheetId}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!res.ok) throw new Error(`Smartsheet API error: ${res.status}`);
  return res.json();
}
```

### Building the row tree

```javascript
// rowTransformer.js
export function buildTree(rows, columns) {
  const colMap = Object.fromEntries(columns.map(c => [c.title, c.id]));
  const getCell = (row, title) =>
    row.cells.find(c => c.columnId === colMap[title])?.displayValue ?? null;

  const nodeMap = {};
  const roots = [];

  for (const row of rows) {
    const node = {
      id: String(row.id),
      parentId: row.parentId ? String(row.parentId) : null,
      indent: row.indent ?? 0,
      name: getCell(row, 'Primary Column'),
      statusEmoji: getCell(row, 'Status'),
      ryg: getCell(row, 'RYG'),
      start: getCell(row, 'Start'),
      finish: getCell(row, 'Finish'),
      duration: getCell(row, 'Duration'),
      predecessors: getCell(row, 'Predecessors'),
      variance: getCell(row, 'Variance2'),
      comments: getCell(row, 'Comments'),
      baselineStart: getCell(row, 'Baseline Start'),
      baselineFinish: getCell(row, 'Baseline Finish'),
      masterScheduleItem: getCell(row, 'Master Schedule Item'),
      children: [],
    };
    nodeMap[node.id] = node;
  }

  for (const node of Object.values(nodeMap)) {
    if (node.parentId && nodeMap[node.parentId]) {
      nodeMap[node.parentId].children.push(node);
    } else {
      roots.push(node);
    }
  }

  return roots;
}
```

---

## Build Order for Claude Code

1. Cloudflare project scaffold — `wrangler.toml`, Vite + React setup, folder structure
2. Worker: `smartsheetClient.js` — fetch sheet via API v2
3. Worker: `rowTransformer.js` — flat rows → nested tree via `parentId`
4. Worker: `scheduleStore.js` — Cloudflare KV read/write
5. Worker: Cron handler — wires steps 2–4 on 6-hour schedule
6. Worker: `auth.js` — Google OAuth, domain restriction to @mytra.ai, role check, signed session cookie
7. Worker: `/api/schedule` endpoint — session-gated, returns KV data
8. Worker: `/api/refresh` endpoint — admin-gated, triggers manual pull
9. Frontend: `AuthContext` + login gate + OAuth redirect handling
10. Frontend: `useSchedule` hook — fetch `/api/schedule`, handle loading/error states
11. Frontend: `GanttChart` + `GanttRow` + `GanttBar` — core rendering with date positioning
12. Frontend: `RYGCircle` component + baseline bar beneath main Gantt bar
13. Frontend: `HoverTooltip` — compact stats on row hover
14. Frontend: `DetailPanel` — full detail side panel on row click, predecessors resolved by name
15. Frontend: `CollapseControls` + `useCollapse` hook
16. Frontend: `FilterBar` + `useFilters` hook
17. Frontend: `TimeScaleToggle` — Day/Week/Month/Quarter axis
18. Frontend: `RefreshButton` — admin-only, last updated timestamp, loading state
19. Frontend: `ThemeToggle` — dark/light, localStorage persistence
20. End-to-end test with live Smartsheet data
21. Cloudflare Pages deployment + `timeline.mytra.ai` custom domain setup

---

## Open Items — Confirm Before Build Starts

1. **TPM email allowlist** — list of @mytra.ai emails that should have Admin access. Goes into Worker secret `ADMIN_EMAILS`.
2. **Google OAuth credentials** — a Google Cloud OAuth 2.0 client ID and secret restricted to `@mytra.ai` domain. Goes into Worker secrets `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`.
3. **Cloudflare KV namespace ID** — created via `wrangler kv:namespace create SCHEDULE_KV`, paste the returned ID into `wrangler.toml`.

---

*Last updated: 2026-03-17 | Version: 0.3*
