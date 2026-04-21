# Socket VDash

> **Time-series security metrics from Socket.dev, visualized in Grafana.**

Socket's native Reports page is great for snapshots — but enterprises need to **trend data over time**, correlate with other observability signals, and embed security metrics into existing Grafana stacks. That's what this project does.

## What It Does

- Polls the Socket API on a configurable interval (default: every 60 min)
- Stores metrics as time-series snapshots in Postgres
- Surfaces them in a pre-built Grafana dashboard with 8 panels

### Dashboard Panels

| Panel | Description |
|---|---|
| Overall Security Score | Org avg trend across 5 score dimensions |
| Total Packages Monitored | Current count stat |
| High Risk Packages | Packages with critical alerts |
| Open CVEs | Distinct CVEs in time window |
| Alert Severity Trend | Stacked bar: critical/high/medium/low |
| Bottom 10 by Supply Chain Score | Table of riskiest packages |
| CVE Findings | Table with CVSS score + fixability |
| Dependency Health Inventory | Direct, transitive, unmaintained, deprecated |

## Prerequisites

- Docker + Docker Compose
- A [Socket.dev](https://socket.dev) account with API token
- At least one repo connected to Socket

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/black-cat-ops/socket-vdash.git
cd socket-vdash

# 2. Configure environment
cp .env.example .env
# Edit .env — add your SOCKET_API_TOKEN and SOCKET_ORG_SLUG

# 3. Launch
docker compose up -d

# 4. Open Grafana
open http://localhost:3000
# Login: admin / admin
```

## Configuration

Edit `.env`:

```env
# Required
SOCKET_API_TOKEN=your_token_here
SOCKET_ORG_SLUG=your_org_slug_here

# Optional
COLLECT_INTERVAL_MINUTES=60   # How often to poll (default: 60)
LOG_LEVEL=INFO                 # DEBUG for verbose output
```

Your org slug is the part of your Socket dashboard URL after `/org/`:
`https://socket.dev/dashboard/org/YOUR_SLUG_HERE`

## Finding Your Org Slug

Go to your Socket dashboard → the URL will show:
```
https://socket.dev/dashboard/org/<your-org-slug>
```

## Architecture

```
Socket API → Python Collector → Postgres → Grafana
                (scheduled)     (time-series   (pre-built
                                 snapshots)     dashboard)
```

All three services run in Docker Compose. Data persists across restarts via named volumes.

## First Run Notes

- The collector runs immediately on startup, then every `COLLECT_INTERVAL_MINUTES`
- If no full scans exist (no repos connected), the collector falls back to the dependency search endpoint
- Grafana dashboard auto-provisions — no manual import needed

## Extending

Each metric is a separate table in Postgres — easy to add new panels in Grafana or new collection logic in `collector/metrics.py`.

Socket is expanding their Reports framework rapidly. This project is designed to complement, not replace, Socket's native reporting — it adds the time-series trending and Grafana integration that enterprise teams already rely on.

## License

MIT
