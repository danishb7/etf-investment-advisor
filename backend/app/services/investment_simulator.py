"""Backtest a saved investment plan using real historical ETF prices."""

from __future__ import annotations

from calendar import monthrange
from collections import defaultdict
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from app.services.market_data import fetch_history


def _parse_date(s: str) -> pd.Timestamp:
    return pd.to_datetime(s).normalize()


def _leg_active(leg: dict, dt: pd.Timestamp, scenario_start: pd.Timestamp, scenario_end: pd.Timestamp) -> bool:
    leg_start = _parse_date(leg["start_date"]) if leg.get("start_date") else scenario_start
    leg_end = _parse_date(leg["end_date"]) if leg.get("end_date") else scenario_end
    return leg_start <= dt <= leg_end


def _monthly_dates(start: pd.Timestamp, end: pd.Timestamp, day_of_month: int) -> list[pd.Timestamp]:
    dates: list[pd.Timestamp] = []
    cur = start.replace(day=1)
    while cur <= end:
        last_day = monthrange(cur.year, cur.month)[1]
        d = min(max(1, day_of_month), last_day)
        candidate = pd.Timestamp(year=cur.year, month=cur.month, day=d)
        if start <= candidate <= end:
            dates.append(candidate)
        cur += pd.DateOffset(months=1)
    return dates


def _build_contribution_schedule(
    start: pd.Timestamp,
    end: pd.Timestamp,
    lump_sum: float,
    monthly_amount: float,
    contribution_day: int,
) -> dict[pd.Timestamp, float]:
    schedule: dict[pd.Timestamp, float] = defaultdict(float)
    if lump_sum > 0:
        schedule[start] += lump_sum
    if monthly_amount > 0:
        for md in _monthly_dates(start, end, contribution_day):
            schedule[md] += monthly_amount
    return dict(schedule)


def _price_on_or_after(prices: pd.Series, dt: pd.Timestamp) -> float | None:
    idx = prices.index
    if dt in idx:
        return float(prices.loc[dt])
    future = idx[idx >= dt]
    if len(future) == 0:
        return None
    return float(prices.loc[future[0]])


def _execute_contribution(
    cash: float,
    dt: pd.Timestamp,
    legs: list[dict],
    shares: dict[str, float],
    price_frames: dict[str, pd.Series],
    scenario_start: pd.Timestamp,
    scenario_end: pd.Timestamp,
) -> list[dict]:
    active = [leg for leg in legs if _leg_active(leg, dt, scenario_start, scenario_end)]
    active_alloc = sum(leg["allocation_pct"] for leg in active)
    if active_alloc <= 0:
        return []
    buys = []
    for leg in active:
        ticker = leg["ticker"].upper()
        portion = cash * (leg["allocation_pct"] / active_alloc)
        price = _price_on_or_after(price_frames[ticker], dt)
        if price and price > 0:
            bought = portion / price
            shares[ticker] += bought
            buys.append({
                "ticker": ticker,
                "amount": round(portion, 2),
                "price": round(price, 2),
                "shares": round(bought, 4),
            })
    return buys


def run_investment_backtest(
    db: Session,
    *,
    start_date: str,
    end_date: str | None,
    lump_sum: float,
    monthly_amount: float,
    contribution_day: int,
    legs: list[dict],
) -> dict:
    if not legs:
        raise ValueError("Add at least one ETF with an allocation percentage")
    if lump_sum <= 0 and monthly_amount <= 0:
        raise ValueError("Set a lump sum and/or monthly installment amount")

    total_alloc = sum(leg["allocation_pct"] for leg in legs)
    if abs(total_alloc - 100) > 0.5:
        raise ValueError(f"Allocations must sum to 100% (currently {total_alloc:.1f}%)")

    contribution_day = max(1, min(28, contribution_day))
    scenario_start = _parse_date(start_date)
    scenario_end = _parse_date(end_date) if end_date else pd.Timestamp.utcnow().normalize()
    if scenario_end < scenario_start:
        raise ValueError("End date must be on or after start date")

    tickers = list({leg["ticker"].upper() for leg in legs})
    price_frames: dict[str, pd.Series] = {}
    for ticker in tickers:
        hist = fetch_history(ticker, "max", db)
        if hist.empty or "Close" not in hist.columns:
            raise ValueError(f"No price history for {ticker}")
        s = hist["Close"].astype(float).copy()
        s.index = pd.to_datetime(s.index).normalize()
        price_frames[ticker] = s.sort_index()

    all_dates = pd.DatetimeIndex([])
    for s in price_frames.values():
        mask = (s.index >= scenario_start) & (s.index <= scenario_end)
        all_dates = all_dates.union(s.index[mask])
    all_dates = all_dates.sort_values()
    if len(all_dates) == 0:
        raise ValueError("No trading days in the selected period")

    schedule = _build_contribution_schedule(
        scenario_start, scenario_end, lump_sum, monthly_amount, contribution_day
    )
    contrib_trading_days: dict[pd.Timestamp, float] = defaultdict(float)
    for planned, amount in schedule.items():
        future = all_dates[all_dates >= planned]
        if len(future) > 0:
            contrib_trading_days[future[0]] += amount

    shares = {t: 0.0 for t in tickers}
    total_invested = 0.0
    contributions_log: list[dict] = []
    series: list[dict] = []

    for dt in all_dates:
        cash = contrib_trading_days.get(dt, 0)
        if cash > 0:
            buys = _execute_contribution(
                cash, dt, legs, shares, price_frames, scenario_start, scenario_end
            )
            if buys:
                total_invested += cash
                contributions_log.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "amount": round(cash, 2),
                    "buys": buys,
                })

        port_value = sum(
            shares[t] * (_price_on_or_after(price_frames[t], dt) or 0) for t in tickers
        )
        series.append({
            "date": dt.strftime("%Y-%m-%d"),
            "value": round(port_value, 2),
            "invested": round(total_invested, 2),
        })

    if total_invested <= 0:
        raise ValueError("No contributions could be executed — check dates and tickers")

    final_value = series[-1]["value"]
    return_pct = (final_value / total_invested - 1) * 100
    vals = pd.Series([p["value"] for p in series])
    peak = vals.cummax()
    max_dd = float(((vals - peak) / peak).min() * 100) if len(vals) > 1 else 0

    holdings = [
        {
            "ticker": t,
            "shares": round(shares[t], 4),
            "last_price": round(float(price_frames[t].iloc[-1]), 2),
            "value": round(shares[t] * float(price_frames[t].iloc[-1]), 2),
        }
        for t in tickers
    ]

    return {
        "start_date": scenario_start.strftime("%Y-%m-%d"),
        "end_date": scenario_end.strftime("%Y-%m-%d"),
        "total_invested": round(total_invested, 2),
        "final_value": round(final_value, 2),
        "return_pct": round(return_pct, 2),
        "max_drawdown": round(max_dd, 2),
        "series": series,
        "contributions": contributions_log,
        "holdings": holdings,
        "ran_at": datetime.utcnow().isoformat(),
    }
