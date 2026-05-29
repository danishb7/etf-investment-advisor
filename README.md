# ETF Investment Advisor

A local-first US ETF investment advisor that learns your goals, scores ETFs with transparent quantitative rules, overlays macro and news sentiment, and helps you simulate and track positions.

**Disclaimer:** Educational information only, not licensed financial advice.

## Features

- Investor onboarding (budget, SIP, horizon, risk, goals)
- Rule-based ETF scoring with explainable breakdowns (momentum, Sharpe, volatility, expense, macro, sentiment)
- Optional ML ranking (off by default; enable with `ML_ENABLED=true` after training)
- FRED macro overlay + RSS/VADER sentiment
- Dashboard with allocation chart, macro regime pills, and recommendations
- ETF universe browser, ticker search, and detail pages with adjustable-period charts
- **Simulate** page: investment plans (multi-ETF backtest), historical what-if, paper holdings, forward Monte Carlo
- Portfolio tracker, rebalancing alerts, tax-loss hints, watchlist
- Minimal aesthetic UI with dark mode and subtle animations

## Prerequisites

- Python 3.11+
- Node.js 18+
- Free [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html) (optional; improves macro overlay and dashboard regime labels)

## Quick start (Windows)

**First time only:** double-click `setup.bat` (creates `backend\venv`, installs dependencies, copies `.env.example` → `.env`).

| Action | Command |
|--------|---------|
| **Start** | Double-click `run.bat` (opens backend + frontend in two windows) |
| **Stop** | Double-click `stop.bat` (frees ports 8000 and 5173) |
| **Tests** | Double-click `test.bat` |
| **Open app** | [http://localhost:5173](http://localhost:5173) |

### Manual start

#### Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\python.exe -m pip install -r requirements.txt
# macOS/Linux:
# python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
# Edit .env and set FRED_API_KEY=your_key (optional)

venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) and complete onboarding.

### FRED API key (optional)

1. Add `FRED_API_KEY=...` to `backend/.env` (no quotes needed for a plain alphanumeric key).
2. Restart the backend.
3. Verify: [http://127.0.0.1:8000/api/macro?force=true](http://127.0.0.1:8000/api/macro?force=true) should show `"available": true`.
4. Macro data is cached in SQLite for 24 hours. If you add a key after first run, use `?force=true` once or click **Refresh** on the dashboard (loads macro with force).

**Note:** Most equity ETFs show **Macro fit ~50** in neutral regimes; only a few categories (e.g. TIPS, gold) move off 50 when inflation/rates rules apply. That is expected scoring behavior, not missing data.

Diagnostic script (from `backend/`):

```bash
set PYTHONPATH=.
venv\Scripts\python.exe scripts\diagnose_fred.py
```

### Optional: train ML model

```bash
cd backend
set PYTHONPATH=.
venv\Scripts\python.exe -m scripts.train_ml
# Set ML_ENABLED=true in .env to blend ML scores into recommendations
```

### Docker (optional)

Requires `backend/.env` (copy from `.env.example` first).

```bash
docker compose up
```

Backend: [http://127.0.0.1:8000](http://127.0.0.1:8000) · Frontend: [http://localhost:5173](http://localhost:5173)

## App pages

| Route | Purpose |
|-------|---------|
| `/onboarding` | First-time investor profile wizard |
| `/` | Dashboard: recommendations, allocation chart, macro & sentiment |
| `/etfs` | Curated ETF universe list |
| `/etfs/:ticker` | ETF detail: price chart, stats, quote refresh |
| `/simulate` | Investment simulator, historical what-if, paper positions, Monte Carlo |
| `/portfolio` | Holdings, rebalancing, tax hints, watchlist |
| `/settings` | Edit profile |

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check (`ml_enabled` flag) |
| `GET` / `PUT` | `/api/profile` | Investor profile |
| `GET` | `/api/recommend?force=` | Recommendations (cached up to `RECOMMENDATION_TTL_MINUTES`, invalidated when profile changes) |
| `POST` | `/api/recommend` | Regenerate recommendations (Refresh) |
| `GET` | `/api/recommend/history` | Past recommendation runs |
| `GET` | `/api/etfs` | Curated universe list |
| `GET` | `/api/etfs/search?q=` | Search curated + optional Yahoo lookup |
| `POST` | `/api/etfs/prefetch` | Warm price cache for universe |
| `GET` | `/api/etfs/{ticker}/history?period=` | OHLCV history (`1m`, `3m`, `6m`, `1y`, `3y`, `5y`, `max`) |
| `GET` | `/api/etfs/{ticker}/quote?refresh=` | Latest cached price |
| `GET` | `/api/macro?force=` | FRED macro snapshot + regime |
| `GET` | `/api/sentiment?force=` | RSS/VADER theme scores |
| `POST` | `/api/simulate/historical` | Single-ETF what-if backtest |
| `POST` | `/api/simulate/forward` | Monte Carlo projection |
| `GET` / `POST` | `/api/paper-positions` | Paper holdings |
| `DELETE` | `/api/paper-positions/{id}` | Remove paper position |
| `GET` / `POST` | `/api/portfolio` | Real holdings |
| `DELETE` | `/api/portfolio/{id}` | Remove holding |
| `GET` | `/api/portfolio/rebalance` | Drift vs last recommendation |
| `GET` | `/api/portfolio/tax-hints` | Informational tax-loss hints |
| `GET` / `POST` / `DELETE` | `/api/watchlist` | Watchlist tickers |
| `GET` / `POST` | `/api/investment-simulator` | List / create saved investment plans |
| `GET` / `PUT` / `DELETE` | `/api/investment-simulator/{id}` | Get / update / delete plan |
| `POST` | `/api/investment-simulator/{id}/run` | Re-run backtest for a plan |

Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Tests

From the repo root (Windows):

```text
test.bat
```

Or manually:

```bash
cd backend
venv\Scripts\python.exe -m pip install -r requirements-dev.txt
venv\Scripts\python.exe -m pytest
```

The suite uses a temporary SQLite database and mocks market-data fetches where needed, so tests do not call Yahoo Finance or FRED live.

GitHub Actions runs `pytest` with coverage (`--cov-fail-under=80`) on every push and pull request (see `.github/workflows/tests.yml`).

Frontend unit tests: `cd frontend && npm test` (Vitest).

### Scoring preferences

- **ESG** (`esg_preference` on profile): +12 boost for ETFs tagged `esg: true` in the curated universe (e.g. ESGV, ESGU, SUSL, VSGX).
- **Shariah**: +2 modest boost always for shariah-tagged funds (SPUS, HLAL, MNZL, SPTE, SPWO).

Set `RECOMMENDATION_TTL_MINUTES=60` in `backend/.env` to control how long cached recommendations are reused.

## Troubleshooting

| Issue | What to try |
|-------|-------------|
| `'uvicorn' is not recognized` | Use `venv\Scripts\python.exe -m uvicorn` (as in `run.bat`), or recreate venv: delete `backend\venv`, run `setup.bat` |
| Macro `available: false` after adding FRED key | Open `/api/macro?force=true`, then restart backend; stale 24h cache is bypassed when key is set but cache was empty |
| Backend reload spam / tracebacks in terminal | `run.bat` excludes `tests/` and `scripts/` from reload; restart with `stop.bat` + `run.bat` if needed |
| Moved or renamed project folder | Delete `backend\venv` and run `setup.bat` again |

## Security

See [SECURITY.md](SECURITY.md). Never commit `.env` or `*.db` files.

## Data sources (free)

- [yfinance](https://github.com/ranaroussi/yfinance): Yahoo Finance prices (unofficial; ~15 min delay typical)
- [FRED](https://fred.stlouisfed.org/): US macro data (API key optional)
- RSS feeds + VADER: News sentiment (no API key)
