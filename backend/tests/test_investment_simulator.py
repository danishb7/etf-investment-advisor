from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from app.services.investment_simulator import (
    _build_contribution_schedule,
    _monthly_dates,
    _price_on_or_after,
    run_investment_backtest,
)


def _mock_history(start="2020-06-01", periods=400, start_price=100.0, end_price=160.0):
    dates = pd.bdate_range(start, periods=periods)
    closes = np.linspace(start_price, end_price, len(dates))
    return pd.DataFrame({"Close": closes}, index=dates)


def test_monthly_dates_respects_contribution_day():
    start = pd.Timestamp("2021-01-15")
    end = pd.Timestamp("2021-04-30")
    dates = _monthly_dates(start, end, day_of_month=15)
    assert len(dates) == 4
    assert all(d.day == 15 for d in dates)


def test_build_contribution_schedule_lump_and_monthly():
    start = pd.Timestamp("2021-01-01")
    end = pd.Timestamp("2021-03-31")
    schedule = _build_contribution_schedule(start, end, lump_sum=1000, monthly_amount=100, contribution_day=1)
    # Lump sum and first monthly installment both land on the 1st.
    assert schedule[start] == pytest.approx(1100, abs=0.01)
    assert sum(schedule.values()) == pytest.approx(1300, abs=0.01)


def test_price_on_or_after_finds_next_trading_day():
    idx = pd.to_datetime(["2021-01-04", "2021-01-05", "2021-01-06"])
    prices = pd.Series([100.0, 101.0, 102.0], index=idx)
    assert _price_on_or_after(prices, pd.Timestamp("2021-01-05")) == 101.0
    assert _price_on_or_after(prices, pd.Timestamp("2021-01-02")) == 100.0
    assert _price_on_or_after(prices, pd.Timestamp("2022-01-01")) is None


def test_run_backtest_validation_errors(db):
    with pytest.raises(ValueError, match="at least one ETF"):
        run_investment_backtest(
            db,
            start_date="2021-01-01",
            end_date="2021-06-01",
            lump_sum=0,
            monthly_amount=0,
            contribution_day=1,
            legs=[],
        )

    with pytest.raises(ValueError, match="Allocations must sum"):
        run_investment_backtest(
            db,
            start_date="2021-01-01",
            end_date="2021-06-01",
            lump_sum=1000,
            monthly_amount=0,
            contribution_day=1,
            legs=[{"ticker": "VTI", "allocation_pct": 50}],
        )


@patch("app.services.investment_simulator.fetch_history")
def test_run_backtest_without_end_date_tz_aware_prices(mock_fetch, db):
    hist = _mock_history()
    hist.index = hist.index.tz_localize("UTC")
    mock_fetch.return_value = hist
    result = run_investment_backtest(
        db,
        start_date="2020-07-01",
        end_date=None,
        lump_sum=1000,
        monthly_amount=0,
        contribution_day=1,
        legs=[{"ticker": "VTI", "allocation_pct": 100}],
    )
    assert result["total_invested"] == 1000
    assert result["final_value"] > 0


@patch("app.services.investment_simulator.fetch_history")
def test_run_backtest_lump_sum_single_etf(mock_fetch, db):
    mock_fetch.return_value = _mock_history()
    result = run_investment_backtest(
        db,
        start_date="2020-07-01",
        end_date="2021-12-31",
        lump_sum=1000,
        monthly_amount=0,
        contribution_day=1,
        legs=[{"ticker": "VTI", "allocation_pct": 100}],
    )
    assert result["total_invested"] == 1000
    assert result["final_value"] > 1000
    assert result["return_pct"] > 0
    assert len(result["series"]) > 0
    assert result["holdings"][0]["ticker"] == "VTI"
    assert len(result["contributions"]) == 1


@patch("app.services.investment_simulator.fetch_history")
def test_create_scenario_api(mock_fetch, client):
    mock_fetch.return_value = _mock_history()
    payload = {
        "name": "Test plan",
        "start_date": "2020-07-01",
        "end_date": "2021-12-31",
        "lump_sum": 500,
        "monthly_amount": 0,
        "contribution_day": 1,
        "legs": [{"ticker": "VTI", "allocation_pct": 100}],
    }
    response = client.post("/api/investment-simulator", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test plan"
    assert data["total_invested"] == 500
    assert data["result"] is not None

    listed = client.get("/api/investment-simulator")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    missing = client.get("/api/investment-simulator/999")
    assert missing.status_code == 404


@patch("app.services.investment_simulator.fetch_history")
def test_create_scenario_rejects_bad_allocation(mock_fetch, client):
    mock_fetch.return_value = _mock_history()
    payload = {
        "name": "Bad plan",
        "start_date": "2020-07-01",
        "lump_sum": 500,
        "monthly_amount": 0,
        "contribution_day": 1,
        "legs": [{"ticker": "VTI", "allocation_pct": 40}],
    }
    response = client.post("/api/investment-simulator", json=payload)
    assert response.status_code == 400
