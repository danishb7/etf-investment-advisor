import json

import numpy as np
import pandas as pd
import pytest

from app.models.models import LastRecommendation, PortfolioHolding
from app.schemas import ForwardSimRequest
from app.services.simulator import (
    check_rebalancing,
    forward_simulation,
    historical_simulation,
    tax_loss_hints,
)


def _hist(n=400):
    dates = pd.bdate_range("2020-01-01", periods=n)
    closes = np.linspace(100, 150, n)
    return pd.DataFrame({"Close": closes}, index=dates)


def test_historical_simulation(db, monkeypatch):
    monkeypatch.setattr("app.services.simulator.fetch_history", lambda t, p, db: _hist())
    r = historical_simulation("VTI", 1000, "2021-01-01", db)
    assert r.final_value > 1000
    assert len(r.series) > 0


def test_forward_simulation(db, monkeypatch):
    monkeypatch.setattr("app.services.simulator.fetch_history", lambda t, p, db: _hist())
    req = ForwardSimRequest(horizon_months=12, tickers=["VTI"], lump_sum=1000, simulations=50)
    r = forward_simulation(req, db)
    assert r.median_final_value > 0
    assert len(r.series) == 13


def test_check_rebalancing(db, monkeypatch):
    db.add(LastRecommendation(allocations_json=json.dumps({"VTI": 60, "BND": 40})))
    db.add(PortfolioHolding(ticker="VTI", shares=10, cost_basis=400))
    db.add(PortfolioHolding(ticker="BND", shares=5, cost_basis=400))
    db.commit()

    def quote(ticker, db):
        return {"price": 100.0 if ticker == "VTI" else 10.0}

    monkeypatch.setattr("app.services.simulator.fetch_quote", quote)
    alerts = check_rebalancing(db, threshold=5.0)
    assert len(alerts) >= 1


def test_tax_loss_hints(db, monkeypatch):
    db.add(PortfolioHolding(ticker="VTI", shares=10, cost_basis=2000))
    db.commit()
    monkeypatch.setattr(
        "app.services.simulator.fetch_quote",
        lambda t, db: {"price": 50.0},
    )
    hints = tax_loss_hints(db)
    assert len(hints) == 1
    assert hints[0].unrealized_loss < 0
