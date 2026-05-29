import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.market_data import (
    compute_stats,
    fetch_fundamentals,
    fetch_history,
    fetch_quote,
    history_to_chart,
    prefetch_universe,
)
from app.services.universe import load_universe

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/etfs", tags=["etfs"])


@router.get("")
def list_etfs():
    universe = load_universe()
    return {"etfs": universe, "count": len(universe)}


@router.post("/prefetch")
def prefetch(db: Session = Depends(get_db)):
    count = prefetch_universe(db)
    return {"prefetched": count}


@router.get("/search")
def search_etfs(q: str = Query(..., min_length=1, max_length=10), db: Session = Depends(get_db)):
    query = q.upper().strip()
    universe = load_universe()
    q_lower = query.lower()

    curated = [
        {**etf, "in_universe": True}
        for etf in universe
        if query in etf["ticker"]
        or q_lower in etf["name"].lower()
        or q_lower in etf.get("category", "").replace("_", " ")
        or q_lower in etf.get("sector", "").replace("_", " ")
    ]

    lookup = None
    in_curated_tickers = {e["ticker"] for e in curated}
    if query not in in_curated_tickers:
        try:
            fund = fetch_fundamentals(query, db)
            hist = fetch_history(query, "1m", db)
            if fund.get("name") or not hist.empty:
                meta = next((e for e in universe if e["ticker"] == query), None)
                lookup = {
                    "ticker": query,
                    "name": fund.get("name") or meta["name"] if meta else query,
                    "category": meta["category"] if meta else "user_search",
                    "sector": meta["sector"] if meta else "other",
                    "in_universe": meta is not None,
                    **fund,
                    "has_data": not hist.empty,
                }
        except Exception as exc:
            logger.warning("etf search lookup failed ticker=%s: %s", query, exc)
            lookup = None

    return {"query": query, "curated": curated, "lookup": lookup}


@router.get("/{ticker}/history")
def get_history(
    ticker: str,
    period: str = Query("1y", pattern="^(1m|3m|6m|1y|3y|5y|max)$"),
    db: Session = Depends(get_db),
):
    hist = fetch_history(ticker.upper(), period, db)
    if hist.empty:
        raise HTTPException(404, f"No history for {ticker}")
    stats = compute_stats(hist)
    return {"ticker": ticker.upper(), "period": period, "data": history_to_chart(hist), "stats": stats}


@router.get("/{ticker}/quote")
def get_quote(ticker: str, refresh: bool = False, db: Session = Depends(get_db)):
    if refresh:
        from app.models.models import PriceCache

        db.query(PriceCache).filter(PriceCache.ticker == ticker.upper()).delete()
        db.commit()
    return fetch_quote(ticker.upper(), db)
