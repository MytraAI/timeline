# TimeLine — Build Plan for Claude Code

> **Status**: Draft v0.2 — All critical assumptions resolved. Ready for build.

---

## Product Overview

TimeLine is an internal web app for Mytra that makes the company's robotics development schedule visible to all employees. The schedule lives in Smartsheet, managed daily by TPMs, and is exported as a CSV to Google Drive every 6 hours via Smartsheet's Data Shuttle. TimeLine reads that CSV, renders it as an interactive Gantt chart, and is accessible to all @mytra.ai Google accounts.

---

## Architecture

```
Smartsheet (TPM daily input)
    ↓ (Smartsheet Data Shuttle — already built, runs every 6 hours)
Google Drive (timestamped .csv files)
    ↓ (Cloudflare Worker cron — every 6 hours)
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
| Data source | Google Drive (CSV via Data Shuttle) |
| Frontend framework | React (via Vite) |
| Styling | Tailwind CSS |

---

## User Roles

| Role | Access |
|---|---|
| Employee | Read-only schedule view |
| Admin (TPM) | Read-only + manual refresh button |

Role is determined at login by checking if the authenticated Google account is on an allowlist of TPM emails stored as a Cloudflare Worker secret (JSON array). No UI for managing this list in v1 — edited manually by the single feature maintainer.

---

## Data Pipeline (The Agent)

### What exists already
- Smartsheet Data Shuttle exports a timestamped `.csv` to a specific Google Drive folder every 6 hours. This is already working and requires no changes.

### What needs to be built

**Cloudflare Worker: `timeline-agent`**

Responsibilities:
1. Authenticate with Google Drive API using a service account
2. Find the most recent `.csv` file in the designated Drive folder (sort by `createdTime` descending, take first)
3. Download and parse the CSV into structured JSON
4. Store result in Cloudflare KV under key `schedule:latest` with a timestamp
5. Expose `/api/schedule` — returns KV contents to authenticated frontend requests
6. Expose `/api/refresh` — manually triggers steps 1–4, restricted to Admin role only

**Trigger schedule:**
- Cloudflare Cron Trigger: every 6 hours, aligned to Data Shuttle export schedule
- Manual trigger: `POST /api/refresh` — callable from the UI by TPMs only

**Google Drive auth:**
- Google Cloud service account with read-only access to the specific Drive folder
- Service account credentials stored as Cloudflare Worker secrets (never in source code)
- Required Google API: Google Drive API v3

---

## CSV Structure

Exact column headers from the exported CSV:

| Column | Type | Notes |
|---|---|---|
| `Status` | String | Hierarchy label / row type indicator |
| `RYG` | String | `"red"`, `"yellow"`, `"green"`, or empty |
| `Primary Column` | String | Task name / row label |
| `Start` | Date | Confirm format with actual file |
| `Finish` | Date | Confirm format with actual file |
| `Duration` | String | e.g. "5 days" |
| `Assignee` | String | Person or team name |
| `% Complete` | Number | 0–100 |
| `Predecessors` | String | Row dependency references — display only in v1 |

**Hierarchy:** Smartsheet indentation level is not a column in CSV exports. Hierarchy must be inferred from the `Status` column values (e.g. "Program", "System", "Subsystem", "Task"). Confirm the exact values used in the `Status` column with the TPM team before building the parser — see Open Items below.

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
- % Complete displayed as a progress fill within the Gantt bar
- Assignee visible on row hover

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

- Filter by RYG status (Red / Yellow / Green) — toggle on/off per color
- Include filter: text search — show only rows whose `Primary Column` matches
- Exclude filter: text search — hide rows whose `Primary Column` matches
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
| RYG circles | Filled circles: red `#ef4444` / yellow `#eab308` / green `#22c55e` |
| Gantt bar | Accent purple, % complete shown as lighter fill within bar |
| Font | Characterful display font for headers, monospace for data/dates |

---

## Cloudflare KV Schema

**Key:** `schedule:latest`

```json
{
  "updatedAt": "2026-03-17T14:00:00Z",
  "sourceFile": "mytra-schedule-2026-03-17T14-00-00.csv",
  "rows": [
    {
      "id": "row-001",
      "name": "Actuator Development",
      "status": "System",
      "ryg": "yellow",
      "start": "2026-01-01",
      "finish": "2026-06-30",
      "duration": "180 days",
      "assignee": "Mech Team",
      "percentComplete": 42,
      "predecessors": "row-000",
      "level": 2,
      "parentId": "row-000",
      "children": []
    }
  ]
}
```

---

## Project File Structure

```
timeline/
├── src/
│   ├── app/                        # React frontend (Cloudflare Pages)
│   │   ├── components/
│   │   │   ├── GanttChart.jsx      # Main chart container
│   │   │   ├── GanttRow.jsx        # Single task row + bar
│   │   │   ├── GanttBar.jsx        # Horizontal timeline bar
│   │   │   ├── RYGCircle.jsx       # Status indicator
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
│       ├── driveClient.js          # Google Drive API v3 integration
│       ├── csvParser.js            # CSV → structured JSON with hierarchy inference
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
GOOGLE_DRIVE_FOLDER_ID = "<DRIVE_FOLDER_ID>"
ALLOWED_DOMAIN = "mytra.ai"

# Secrets (set via wrangler CLI, never in code):
# GOOGLE_SERVICE_ACCOUNT_JSON
# ADMIN_EMAILS
# SESSION_SECRET
```

---

## Google Cloud Setup (one-time, done by maintainer)

1. Open Google Cloud Console — use existing Mytra Google Cloud project
2. Enable **Google Drive API**
3. Create a **Service Account** with no roles
4. Download the service account JSON key
5. Share the Google Drive folder (CSV destination) with the service account email — **Viewer** access only
6. Store the JSON key as Cloudflare Worker secret: `wrangler secret put GOOGLE_SERVICE_ACCOUNT_JSON`

---

## Build Order for Claude Code

1. Cloudflare project scaffold — `wrangler.toml`, Vite + React setup, folder structure
2. Worker: `driveClient.js` — authenticate + find + download latest CSV
3. Worker: `csvParser.js` — CSV → JSON, hierarchy inference from `Status` column values
4. Worker: `scheduleStore.js` — KV read/write
5. Worker: Cron handler — wires steps 2–4 on 6-hour schedule
6. Worker: `auth.js` — Google OAuth, domain restriction, role check, signed session cookie
7. Worker: `/api/schedule` endpoint — session-gated, returns KV data
8. Worker: `/api/refresh` endpoint — admin-gated, triggers manual pull
9. Frontend: `AuthContext` + login gate + OAuth redirect handling
10. Frontend: `useSchedule` hook — fetch `/api/schedule`, handle loading/error states
11. Frontend: `GanttChart` + `GanttRow` + `GanttBar` — core rendering with date positioning
12. Frontend: `RYGCircle` component + `% Complete` fill within Gantt bar
13. Frontend: `CollapseControls` + `useCollapse` hook
14. Frontend: `FilterBar` + `useFilters` hook
15. Frontend: `TimeScaleToggle` — Day/Week/Month/Quarter axis
16. Frontend: `RefreshButton` — admin-only, last updated timestamp, loading state
17. Frontend: `ThemeToggle` — dark/light, localStorage persistence
18. End-to-end test with real CSV from Google Drive
19. Cloudflare Pages deployment + custom domain setup

---

## Open Items — Confirm Before Build Starts

1. **`Status` column values** — What are the exact text values used in the Status column to indicate hierarchy level? The CSV parser hierarchy inference depends on knowing these precisely (e.g. "Program", "System", "Subsystem", "Task").
2. **Google Drive folder ID** — The folder ID from the Drive URL where Data Shuttle drops the CSVs. Goes into `wrangler.toml` as `GOOGLE_DRIVE_FOLDER_ID`.
3. **Date format** — Confirm Start/Finish columns export as MM/DD/YYYY or YYYY-MM-DD by checking an actual exported file.
4. **TPM email list** — List of @mytra.ai emails that should have Admin access. Goes into Worker secret `ADMIN_EMAILS`.
5. **Custom domain** — What URL should TimeLine be served at? (e.g. `timeline.mytra.ai`)

---

*Last updated: 2026-03-17 | Version: 0.2*
