import json
import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import FundamentalCache, PriceCache
from app.services.universe import load_universe

logger = logging.getLogger(__name__)

PERIOD_MAP = {
    "1m": "1mo",
    "3m": "3mo",
    "6m": "6mo",
    "1y": "1y",
    "3y": "3y",
    "5y": "5y",
    "max": "max",
}


def _cache_fresh(fetched_at: datetime) -> bool:
    ttl = timedelta(minutes=settings.price_cache_ttl_minutes)
    return datetime.utcnow() - fetched_at < ttl


def fetch_history(ticker: str, period: str = "1y", db: Session | None = None) -> pd.DataFrame:
    yf_period = PERIOD_MAP.get(period.lower(), "1y")
    if db:
        cached = (
            db.query(PriceCache)
            .filter(PriceCache.ticker == ticker.upper(), PriceCache.period == period.lower())
            .order_by(PriceCache.fetched_at.desc())
            .first()
        )
        if cached and _cache_fresh(cached.fetched_at):
            logger.debug("price cache HIT ticker=%s period=%s", ticker, period)
            records = json.loads(cached.data_json)
            df = pd.DataFrame(records)
            if not df.empty and "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"])
                df = df.set_index("Date")
                return df
            if not df.empty:
                return df.set_index(df.columns[0])
            return df

    logger.info("price cache MISS ticker=%s period=%s", ticker, period)
    t = yf.Ticker(ticker.upper())
    hist = t.history(period=yf_period, auto_adjust=True)
    if hist.empty:
        return hist

    hist = hist.reset_index()
    hist["Date"] = hist["Date"].dt.strftime("%Y-%m-%d")
    records = hist[["Date", "Open", "High", "Low", "Close", "Volume"]].to_dict(orient="records")

    if db:
        db.query(PriceCache).filter(
            PriceCache.ticker == ticker.upper(), PriceCache.period == period.lower()
        ).delete()
        db.add(
            PriceCache(
                ticker=ticker.upper(),
                period=period.lower(),
                data_json=json.dumps(records),
            )
        )
        db.commit()

    df = pd.DataFrame(records)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.set_index("Date")


def fetch_quote(ticker: str, db: Session | None = None) -> dict:
    hist = fetch_history(ticker, "1m", db)
    if hist.empty:
        t = yf.Ticker(ticker.upper())
        info = t.fast_info
        price = getattr(info, "last_price", None) or getattr(info, "previous_close", None)
        return {"ticker": ticker.upper(), "price": float(price) if price else None, "as_of": datetime.utcnow().isoformat()}
    last = hist.iloc[-1]
    return {
        "ticker": ticker.upper(),
        "price": float(last["Close"]),
        "as_of": str(hist.index[-1]),
    }


def fetch_fundamentals(ticker: str, db: Session | None = None) -> dict:
    if db:
        cached = db.query(FundamentalCache).filter(FundamentalCache.ticker == ticker.upper()).first()
        if cached and _cache_fresh(cached.fetched_at):
            logger.debug("fundamental cache HIT ticker=%s", ticker)
            return json.loads(cached.data_json)

    logger.info("fundamental cache MISS ticker=%s", ticker)
    t = yf.Ticker(ticker.upper())
    info = t.info
    data = {
        "ticker": ticker.upper(),
        "expense_ratio": info.get("annualReportExpenseRatio") or info.get("expenseRatio"),
        "dividend_yield": info.get("dividendYield") or info.get("yield"),
        "aum": info.get("totalAssets"),
        "name": info.get("shortName") or info.get("longName", ticker),
        "category": info.get("category"),
    }
    if data["expense_ratio"] and data["expense_ratio"] > 1:
        data["expense_ratio"] = data["expense_ratio"] / 100

    if db:
        existing = db.query(FundamentalCache).filter(FundamentalCache.ticker == ticker.upper()).first()
        if existing:
            existing.data_json = json.dumps(data)
            existing.fetched_at = datetime.utcnow()
        else:
            db.add(FundamentalCache(ticker=ticker.upper(), data_json=json.dumps(data)))
        db.commit()

    return data


def prefetch_universe(db: Session) -> int:
    count = 0
    for etf in load_universe():
        try:
            fetch_history(etf["ticker"], "1y", db)
            fetch_fundamentals(etf["ticker"], db)
            count += 1
        except Exception as exc:
            logger.warning("prefetch failed ticker=%s: %s", etf["ticker"], exc)
            continue
    return count


def compute_stats(hist: pd.DataFrame) -> dict:
    if hist.empty or "Close" not in hist.columns:
        return {}
    closes = hist["Close"].astype(float)
    returns = closes.pct_change().dropna()
    if len(returns) < 2:
        return {}

    total_return = (closes.iloc[-1] / closes.iloc[0] - 1) * 100
    vol = float(returns.std() * np.sqrt(252) * 100)
    sharpe = float((returns.mean() / returns.std()) * np.sqrt(252)) if returns.std() > 0 else 0

    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.cummax()
    drawdown = (cumulative - rolling_max) / rolling_max
    max_dd = float(drawdown.min() * 100)

    return {
        "return_pct": round(total_return, 2),
        "volatility": round(vol, 2),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown": round(max_dd, 2),
    }


def history_to_chart(hist: pd.DataFrame) -> list[dict]:
    if hist.empty:
        return []
    out = []
    for idx, row in hist.iterrows():
        date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)
        out.append({
            "date": date_str,
            "open": float(row.get("Open", row["Close"])),
            "high": float(row.get("High", row["Close"])),
            "low": float(row.get("Low", row["Close"])),
            "close": float(row["Close"]),
            "volume": int(row.get("Volume", 0)),
        })
    return out
