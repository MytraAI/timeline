# TimeLine — Build Plan for Claude Code

> **Status**: Draft v0.1 — Contains open assumptions marked with `⚠️ ASSUMPTION` that must be resolved before building.

---

## Product Overview

TimeLine is an internal web app for Mytra that makes the company's robotics development schedule visible to all employees. The schedule lives in Smartsheet, managed daily by TPMs, and is exported as a CSV to Google Drive on a 6-hour interval. TimeLine reads that CSV, renders it as an interactive Gantt-style schedule, and is accessible to all @mytra.ai Google accounts.

---

## Architecture

```
Smartsheet (TPM daily input)
    ↓ (automated CSV export, every 6 hours — already built)
Google Drive (timestamped .csv files)
    ↓ (TimeLine Agent — pulls latest CSV)
Cloudflare (hosting + serverless)
    ↓
TimeLine Web App (served to authenticated users)
```

### Stack

| Layer | Technology |
|---|---|
| Hosting | Cloudflare Pages |
| Serverless functions | Cloudflare Workers |
| Auth | Google OAuth 2.0, restricted to @mytra.ai domain |
| Data source | Google Drive (CSV) |
| Frontend framework | React (via Vite) |
| Styling | Tailwind CSS |
| State / data | ⚠️ ASSUMPTION: CSV parsed and served as JSON from a Worker |

---

## Data Pipeline (The Agent)

### What exists already
- Smartsheet exports a timestamped `.csv` to Google Drive every 6 hours. This is already working.

### What needs to be built

**Cloudflare Worker: `timeline-agent`**

Responsibilities:
1. Authenticate with Google Drive API using a service account
2. Find the most recent `.csv` file in the designated Drive folder
3. Parse the CSV into structured JSON
4. Store the result in Cloudflare KV (key-value store) with a timestamp
5. Expose a `/api/schedule` endpoint that the frontend reads

**Trigger schedule:**
- Cloudflare Cron Trigger set to every 6 hours
- ⚠️ ASSUMPTION: Manual push trigger is a protected endpoint (`/api/refresh`) callable from a button in the UI, restricted to authenticated users

**Google Drive auth:**
- Use a Google Service Account with read-only access to the specific Drive folder
- Store credentials as Cloudflare Worker secrets (never in code)

---

## CSV Structure

⚠️ ASSUMPTION: Based on described hierarchy, the CSV contains columns roughly like:

| Column | Notes |
|---|---|
| Task Name | Primary label, indentation level indicates hierarchy |
| Level / Indent | Hierarchy depth (Program → System → Subsystem → Task) |
| Start Date | ISO or MM/DD/YYYY format |
| End Date | ISO or MM/DD/YYYY format |
| Status (RYG) | String: "Red", "Yellow", "Green" — ⚠️ MUST CONFIRM this survives CSV export |
| % Complete | Numeric 0–100 — ⚠️ CONFIRM column name |
| Owner | Optional — include if present |

> **Critical open question**: Smartsheet's row color formatting does NOT export to CSV by default. If RYG is a native Smartsheet color and not a dedicated column, it will be lost in the CSV. This must be verified before building.

---

## Authentication

- Google OAuth 2.0
- Domain restriction: `@mytra.ai` only — any other domain is rejected at login
- No role-based access control in v1 — all authenticated users have identical read-only access
- ⚠️ ASSUMPTION: TPMs do not have any write or admin capabilities through the UI in v1

**Implementation:**
- Cloudflare Pages handles auth via Google OAuth
- Use `cloudflare/pages-plugin-oauth2` or implement a Worker-based OAuth flow
- Session stored in a signed cookie

---

## Frontend

### Views

**Primary view: Gantt / Schedule**
- Hierarchical row list with collapsible levels
- Timeline bars rendered on a horizontal axis
- ⚠️ ASSUMPTION: This is a rendered Gantt (bars), not just a data table — confirm this

**Time scale controls:**
- Day / Week / Month / Quarter toggle
- Default view: Week

**Collapse / Expand controls:**
- Collapse All
- Expand All
- Collapse One Level
- Expand One Level

**Filters:**
- Filter by Status (Red / Yellow / Green)
- Include filter (show only matching rows)
- Exclude filter (hide matching rows)
- ⚠️ ASSUMPTION: Filters operate on Task Name text and Status column only in v1

### Status Visualization

| Status | Color |
|---|---|
| Green | `#22c55e` |
| Yellow | `#eab308` |
| Red | `#ef4444` |
| % Complete | Progress bar within the task row |

### Design Spec

| Property | Value |
|---|---|
| Primary accent | `rgb(85, 53, 243)` |
| Default theme | Dark mode |
| Theme toggle | Dark / Light |
| Aesthetic | Clean, bold, minimal chrome |
| Font | TBD — something characterful, not Inter |
| Buttons | Minimal — only what is necessary |

---

## Cloudflare Project Structure

```
timeline/
├── src/
│   ├── app/               # React frontend
│   │   ├── components/
│   │   │   ├── GanttChart.jsx
│   │   │   ├── TaskRow.jsx
│   │   │   ├── FilterBar.jsx
│   │   │   ├── TimeScaleToggle.jsx
│   │   │   └── StatusBadge.jsx
│   │   ├── hooks/
│   │   │   └── useSchedule.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── worker/            # Cloudflare Worker (agent)
│       ├── index.js       # Router: /api/schedule, /api/refresh, /auth/*
│       ├── driveClient.js # Google Drive API integration
│       └── csvParser.js   # CSV → JSON transformer
├── public/
├── wrangler.toml          # Cloudflare config
├── vite.config.js
└── package.json
```

---

## Cloudflare KV Schema

Key: `schedule:latest`

```json
{
  "updatedAt": "2026-03-17T14:00:00Z",
  "source": "mytra-schedule-2026-03-17.csv",
  "rows": [
    {
      "id": "row-001",
      "name": "Actuator Development",
      "level": 2,
      "parentId": "row-000",
      "startDate": "2026-01-01",
      "endDate": "2026-06-30",
      "status": "Yellow",
      "percentComplete": 42,
      "children": []
    }
  ]
}
```

---

## Open Questions — Must Resolve Before Building

1. **RYG in CSV**: Is "Status" a dedicated text column in Smartsheet, or is it Smartsheet's native row color? If it's native color, it will NOT appear in the CSV export and the approach changes significantly.

2. **Gantt bars vs. table**: Is the primary view a true rendered Gantt chart (horizontal bars on a timeline), or a hierarchical list/table with date columns? This is a large scope difference.

3. **Google Drive folder**: What is the folder ID or path where CSVs are being dropped? The Worker needs this hardcoded or as an env var.

4. **Manual refresh**: Should the refresh button be visible to all users or only TPMs? Is there any distinction between user types in v1?

5. **Cloudflare familiarity**: Has Cloudflare Pages/Workers been used before on this project, or is this a fresh setup? Determines how much scaffolding instruction is needed.

6. **CSV column names**: Share the exact column headers from the CSV so the parser is built correctly from day one.

7. **Google Service Account**: Does a Google Cloud project exist for Mytra, or does one need to be created? The Drive API requires this.

---

## Build Order for Claude Code

1. `wrangler.toml` + project scaffold
2. Google Drive service account setup instructions
3. Worker: CSV fetch + parse + KV store
4. Worker: Cron trigger + `/api/schedule` endpoint
5. Worker: Google OAuth flow + domain restriction
6. Frontend: Auth gate
7. Frontend: Schedule data fetch + state
8. Frontend: Gantt rendering (rows + bars)
9. Frontend: Collapse/expand logic
10. Frontend: Filters
11. Frontend: Time scale toggle
12. Frontend: Dark/light theme
13. Manual refresh button + `/api/refresh` endpoint

---

*Last updated: 2026-03-17 | Version: 0.1-draft*
