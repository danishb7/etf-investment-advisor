import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from app.models.models import FundamentalCache, PriceCache
from app.services.market_data import compute_stats, fetch_fundamentals, fetch_history, history_to_chart


def _hist_df(n=300):
    dates = pd.bdate_range("2022-01-01", periods=n)
    prices = 100 * np.cumprod(1 + np.random.default_rng(0).normal(0.001, 0.01, n))
    return pd.DataFrame(
        {"Open": prices, "High": prices, "Low": prices, "Close": prices, "Volume": 1_000_000},
        index=dates,
    )


def test_compute_stats_nonempty():
    stats = compute_stats(_hist_df())
    assert "return_pct" in stats
    assert "sharpe_ratio" in stats
    assert stats["volatility"] > 0


def test_compute_stats_empty():
    assert compute_stats(pd.DataFrame()) == {}


def test_fetch_history_uses_cache(db):
    records = [
        {"Date": "2024-01-02", "Open": 1, "High": 1, "Low": 1, "Close": 100, "Volume": 1},
        {"Date": "2024-01-03", "Open": 1, "High": 1, "Low": 1, "Close": 101, "Volume": 1},
    ]
    db.add(
        PriceCache(
            ticker="VTI",
            period="1y",
            data_json=json.dumps(records),
            fetched_at=datetime.utcnow(),
        )
    )
    db.commit()
    df = fetch_history("VTI", "1y", db)
    assert not df.empty
    assert float(df.iloc[-1]["Close"]) == 101.0


def test_fetch_fundamentals_cache(db):
    data = {"ticker": "VTI", "expense_ratio": 0.03, "name": "VTI"}
    db.add(
        FundamentalCache(
            ticker="VTI",
            data_json=json.dumps(data),
            fetched_at=datetime.utcnow(),
        )
    )
    db.commit()
    assert fetch_fundamentals("VTI", db)["expense_ratio"] == 0.03


def test_history_to_chart():
    df = _hist_df(10)
    chart = history_to_chart(df)
    assert len(chart) == 10
    assert "close" in chart[0]
