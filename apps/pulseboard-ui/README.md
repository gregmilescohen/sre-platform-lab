# pulseboard-ui

React dashboard that polls the PulseBoard API and renders a live event-rate chart, broken
down by event type. Built with Vite, TypeScript, and Recharts.

## What it shows

A line chart of events per minute over the last hour, with one colored line per event type
(`page_view`, `button_click`, `api_call`, `search`, `checkout`, `login`, `error`). Data is
fetched from `GET /api/events/?bucket=minute` every 10 seconds and can be manually refreshed.

## Architecture

In Docker, the production build is served by nginx on port 5173. nginx also proxies
`/api/*` → `pulseboard-api:8080/*`, so the frontend never makes cross-origin requests.

```
browser → nginx :5173
              /api/* → pulseboard-api:8080
              /*     → dist/ (Vite build)
```

For local development outside Docker, Vite's dev server proxies `/api` to `localhost:8080`.

## Running Locally

```bash
npm install
npm run dev        # Vite dev server on :5173 with HMR
npm run build      # Production build → dist/
npm run lint       # ESLint + TypeScript type check
npm run test       # Vitest (watch mode)
npm run test:ci    # Vitest (single run, with coverage)
```

## Environment

No environment variables — the API URL is always `/api/` (relative), resolved by either
nginx (Docker) or Vite's dev proxy (local).
