import numpy as np
import pandas as pd
import pytest

from app.models.models import InvestorProfile
from app.services.fred import macro_fit_score
from app.services.scoring import (
    _allocate,
    _correlation_filter,
    _dividend_score,
    _expense_score,
    _momentum_score,
    _sharpe_score,
    _volatility_score,
)


def _price_frame(ticker: str, returns: np.ndarray, start="2022-01-03") -> pd.DataFrame:
    dates = pd.bdate_range(start, periods=len(returns) + 1)
    prices = 100 * np.cumprod(np.concatenate([[1.0], 1 + returns]))
    return pd.DataFrame({"Close": prices[: len(dates)]}, index=dates[: len(prices)])


def test_momentum_score_rising_prices():
    closes = pd.Series(np.linspace(100, 150, 300))
    hist = pd.DataFrame({"Close": closes})
    score = _momentum_score(hist, horizon_months=60)
    assert score > 50


def test_momentum_score_empty_history_defaults():
    assert _momentum_score(pd.DataFrame(), horizon_months=60) == 50.0


def test_sharpe_score_bounds():
    assert _sharpe_score({"sharpe_ratio": 2}) == 100
    assert _sharpe_score({"sharpe_ratio": -2}) == 0


def test_volatility_score_respects_risk_cap():
    assert _volatility_score({"volatility": 5}, "conservative") == 90
    assert _volatility_score({"volatility": 10}, "conservative") == 70
    assert _volatility_score({"volatility": 30}, "conservative") == 15


def test_expense_score_penalizes_high_fees():
    assert _expense_score(0.001, max_er=0.5) > _expense_score(0.008, max_er=0.5)
    assert _expense_score(0.01, max_er=0.5) == 10.0


def test_dividend_score_income_goal():
    assert _dividend_score(0.03, "income") > _dividend_score(0.03, "wealth_building")


def test_correlation_filter_drops_redundant_pair():
    returns = np.random.default_rng(42).normal(0.0005, 0.01, 120)
    voo = _price_frame("VOO", returns)
    ivv = _price_frame("IVV", returns)
    candidates = [
        {"ticker": "VOO", "final_score": 90},
        {"ticker": "IVV", "final_score": 85},
        {"ticker": "QQQ", "final_score": 80},
    ]
    qqq_returns = np.random.default_rng(7).normal(0.0008, 0.015, 120)
    selected = _correlation_filter(
        candidates,
        {"VOO": voo, "IVV": ivv, "QQQ": _price_frame("QQQ", qqq_returns)},
    )
    tickers = [c["ticker"] for c in selected]
    assert "VOO" in tickers
    assert "IVV" not in tickers
    assert "QQQ" in tickers


def test_allocate_sums_to_one_hundred():
    profile = InvestorProfile(risk_tolerance="balanced")
    picks = [
        {"ticker": "VTI", "final_score": 80},
        {"ticker": "BND", "final_score": 70},
        {"ticker": "VXUS", "final_score": 65},
    ]
    allocated = _allocate(picks, profile)
    assert len(allocated) <= 6
    assert sum(p["allocation_pct"] for p in allocated) == pytest.approx(100.0, abs=0.2)


def test_macro_fit_score_tips_in_elevated_inflation():
    regime = {"rates": "neutral", "inflation": "elevated"}
    tips = macro_fit_score("inflation_protected", "bonds", regime)
    neutral = macro_fit_score("inflation_protected", "bonds", {"rates": "neutral", "inflation": "neutral"})
    assert tips > neutral
