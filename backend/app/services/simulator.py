from datetime import datetime

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.schemas import (
    ForwardSimRequest,
    ForwardSimResponse,
    HistoricalSimPoint,
    HistoricalSimResponse,
    RebalanceAlert,
    TaxLossHint,
)
from app.services.market_data import fetch_history, fetch_quote
from app.models.models import LastRecommendation, PortfolioHolding


def historical_simulation(ticker: str, amount: float, start_date: str, db: Session) -> HistoricalSimResponse:
    hist = fetch_history(ticker, "max", db)
    if hist.empty:
        raise ValueError(f"No data for {ticker}")

    hist = hist.reset_index()
    date_col = "Date" if "Date" in hist.columns else hist.columns[0]
    hist[date_col] = pd.to_datetime(hist[date_col])
    start = pd.to_datetime(start_date)
    subset = hist[hist[date_col] >= start].copy()
    if subset.empty:
        raise ValueError(f"No data after {start_date}")

    first_price = float(subset.iloc[0]["Close"])
    shares = amount / first_price
    series = []
    values = []
    for _, row in subset.iterrows():
        val = shares * float(row["Close"])
        values.append(val)
        series.append(HistoricalSimPoint(date=row[date_col].strftime("%Y-%m-%d"), value=round(val, 2)))

    final_value = values[-1]
    return_pct = (final_value / amount - 1) * 100
    vals = pd.Series(values)
    peak = vals.cummax()
    dd = ((vals - peak) / peak).min() * 100

    return HistoricalSimResponse(
        ticker=ticker.upper(),
        initial_amount=amount,
        final_value=round(final_value, 2),
        return_pct=round(return_pct, 2),
        max_drawdown=round(dd, 2),
        series=series,
    )


def forward_simulation(req: ForwardSimRequest, db: Session) -> ForwardSimResponse:
    tickers = req.tickers or ["VTI"]
    ticker = tickers[0]
    hist = fetch_history(ticker, "5y", db)
    if hist.empty or len(hist) < 60:
        raise ValueError("Insufficient history for simulation")

    returns = hist["Close"].astype(float).pct_change().dropna()
    mu = returns.mean() * 12
    sigma = returns.std() * np.sqrt(12)

    months = req.horizon_months
    monthly = req.monthly_amount or 0
    lump = req.lump_sum or 0
    n_sims = min(req.simulations, 2000)

    finals = []
    median_path = []

    for _ in range(n_sims):
        value = lump
        path = [value]
        for _m in range(months):
            monthly_ret = np.random.normal(mu / 12, sigma / np.sqrt(12))
            value = value * (1 + monthly_ret) + monthly
            path.append(value)
        finals.append(value)
        if len(median_path) < months + 1:
            median_path = path

    finals_arr = np.array(finals)
    return ForwardSimResponse(
        median_final_value=round(float(np.median(finals_arr)), 2),
        percentile_10=round(float(np.percentile(finals_arr, 10)), 2),
        percentile_90=round(float(np.percentile(finals_arr, 90)), 2),
        series=[{"month": i, "value": round(v, 2)} for i, v in enumerate(median_path)],
    )


def check_rebalancing(db: Session, threshold: float = 5.0) -> list[RebalanceAlert]:
    import json

    last = db.query(LastRecommendation).first()
    holdings = db.query(PortfolioHolding).all()
    if not last or not holdings:
        return []

    targets = json.loads(last.allocations_json or "{}")
    if not targets:
        return []

    values = {}
    total = 0.0
    for h in holdings:
        q = fetch_quote(h.ticker, db)
        price = q.get("price") or 0
        val = h.shares * price
        values[h.ticker] = val
        total += val

    if total <= 0:
        return []

    alerts = []
    for ticker, target_pct in targets.items():
        current_pct = values.get(ticker, 0) / total * 100
        drift = abs(current_pct - target_pct)
        if drift > threshold:
            action = "reduce" if current_pct > target_pct else "increase"
            alerts.append(
                RebalanceAlert(
                    ticker=ticker,
                    current_pct=round(current_pct, 1),
                    target_pct=target_pct,
                    drift_pct=round(drift, 1),
                    action=action,
                )
            )
    return alerts


def tax_loss_hints(db: Session) -> list[TaxLossHint]:
    hints = []
    for h in db.query(PortfolioHolding).all():
        if h.cost_basis is None:
            continue
        q = fetch_quote(h.ticker, db)
        price = q.get("price")
        if not price:
            continue
        current = h.shares * price
        loss = current - h.cost_basis
        if loss < -50:
            hints.append(
                TaxLossHint(
                    ticker=h.ticker,
                    unrealized_loss=round(loss, 2),
                    suggestion=f"Unrealized loss of ${abs(loss):.0f} — consult a tax professional about harvesting",
                )
            )
    return hints
