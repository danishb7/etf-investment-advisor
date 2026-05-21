# Security & Privacy

## What stays on your machine

- Investor profile (budget, goals, risk settings)
- Paper positions and real portfolio holdings (if entered)
- Recommendation run history
- Cached market data (SQLite `advisor.db`)

## Never commit to Git

- `backend/.env` — API keys and secrets
- `backend/advisor.db` or any `*.db` file
- `backend/data/cache/`
- `venv/`, `node_modules/`

Only commit `backend/.env.example` with empty placeholders.

## API keys

- **FRED_API_KEY** — stored in backend `.env` only; never sent to the frontend
- No keys required for yfinance or RSS sentiment

## Network

- Default setup: frontend proxies `/api` to `localhost:8000`
- CORS is restricted to local dev origins (`localhost:5173`)
- Market data requests go from your machine to Yahoo (via yfinance), FRED, and public RSS feeds

## Logging

- Do not enable verbose logging of dollar amounts in production-like deployments
- Profile and holdings exist only in your local SQLite file

## Rotating keys

If `FRED_API_KEY` is exposed, regenerate it at [FRED](https://fred.stlouisfed.org/docs/api/api_key.html) and update `.env`.

## Optional hardening

- Encrypt SQLite at rest (future enhancement)
- Add local authentication if deploying beyond localhost
