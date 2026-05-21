# ETF Investment Advisor

A local-first US ETF investment advisor that learns your goals, scores ETFs with transparent quantitative rules, overlays macro and news sentiment, and helps you simulate and track positions.

**Disclaimer:** Educational information only — not licensed financial advice.

## Features

- Investor onboarding (budget, SIP, horizon, risk, goals)
- Rule-based ETF scoring with explainable breakdowns
- Optional ML ranking (off by default)
- FRED macro overlay + RSS/VADER sentiment
- Dashboard with allocation chart and recommendations
- ETF detail pages with adjustable-period charts
- **Investment Simulator** — saved plans with lump sum + monthly installments on a fixed day, multi-ETF allocations, per-ETF date ranges, real historical backtest
- Historical what-if (single ETF) and paper portfolio trackers
- Forward Monte Carlo projection (probabilistic, not historical)
- Portfolio tracker, rebalancing alerts, tax-loss hints, watchlist
- Minimal aesthetic UI with dark mode and subtle animations

## Prerequisites

- Python 3.11+
- Node.js 18+
- Free [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html) (optional but recommended for macro)

## Quick start (Windows)

**First time only:** double-click `setup.bat` (installs Python + npm dependencies).

| Action | Command |
|--------|---------|
| **Start** | Double-click `run.bat` — opens backend + frontend in two windows |
| **Stop** | Double-click `stop.bat` — frees ports 8000 and 5173 |
| **Open app** | [http://localhost:5173](http://localhost:5173) |

### Manual start

#### Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
# Edit .env and add FRED_API_KEY=

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) and complete onboarding.

### Optional: train ML model

```bash
cd backend
python -m scripts.train_ml
# Set ML_ENABLED=true in .env to blend ML scores
```

### Docker (optional)

```bash
docker compose up
```

## API

| Endpoint | Description |
|----------|-------------|
| `GET/PUT /api/profile` | Investor profile |
| `POST /api/recommend` | Generate recommendations |
| `GET /api/etfs/{ticker}/history?period=1y` | Price history |
| `POST /api/simulate/historical` | What-if simulation |
| `GET/POST /api/paper-positions` | Paper holdings |
| `POST /api/simulate/forward` | Monte Carlo projection |
| `GET/POST /api/investment-simulator` | Saved investment plans + historical backtest |

## Tests

From the repo root (Windows):

```text
test.bat
```

Or manually:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

The suite uses an isolated SQLite database and mocks market-data fetches where needed, so tests do not call Yahoo Finance or FRED.

## Security

See [SECURITY.md](SECURITY.md). Never commit `.env` or `*.db` files.

## Data sources (free)

- [yfinance](https://github.com/ranaroussi/yfinance) — Yahoo Finance prices
- [FRED](https://fred.stlouisfed.org/) — US macro data
- RSS feeds + VADER — News sentiment
