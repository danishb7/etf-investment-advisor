# Security & Privacy

## What stays on your machine

- Investor profile (budget, goals, risk settings)
- Paper positions and real portfolio holdings (if entered)
- Saved investment simulator scenarios
- Recommendation run history
- Cached market, macro, and sentiment data in SQLite (`backend/advisor.db` by default)

## Never commit to Git

- `backend/.env`: API keys and secrets
- `backend/advisor.db` or any `*.db` / `*.sqlite` file
- `venv/`, `node_modules/`, `frontend/dist/`
- `.pytest_cache/`, `__pycache__/`

Only commit `backend/.env.example` with empty placeholders.

## API keys

- **FRED_API_KEY**: stored in `backend/.env` only; loaded by the backend via `app.config`; never sent to the frontend
- No keys required for yfinance or RSS sentiment

If a key is exposed, regenerate it at [FRED](https://fred.stlouisfed.org/docs/api/api_key.html) and update `.env`. Do not paste keys into issues, chat logs, or commits.

## Network

- Default dev setup: Vite proxies `/api` to `http://127.0.0.1:8000` (see `frontend/vite.config.ts`)
- CORS allows local dev origins from `CORS_ORIGINS` in `.env` (default `http://localhost:5173`, `http://127.0.0.1:5173`)
- Outbound requests from your machine go to Yahoo (yfinance), FRED (if key set), and public RSS feeds

## Logging

- Avoid logging profile balances or holdings at INFO level in shared or production-like environments
- Uvicorn access logs show paths and status codes only, not response bodies

## Local database

Price, fundamental, macro, and sentiment caches are stored in **SQLite tables** inside `advisor.db`, not as separate files under `backend/data/`. The database file is gitignored.

## Optional hardening

- Encrypt SQLite at rest (not implemented)
- Add local authentication before exposing the app beyond localhost
- Run `pip audit` / `npm audit` periodically for dependency vulnerabilities
