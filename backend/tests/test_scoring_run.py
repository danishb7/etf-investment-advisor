import pandas as pd
import pytest

from app.models.models import InvestorProfile
from app.services.scoring import run_recommendations


@pytest.fixture
def onboarded_profile(db):
    p = InvestorProfile(
        lump_sum=5000,
        monthly_sip=200,
        horizon_months=60,
        risk_tolerance="balanced",
        goal="wealth_building",
        onboarding_complete=True,
        esg_preference=True,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def test_run_recommendations_mocked(db, onboarded_profile, monkeypatch):
    hist = pd.DataFrame(
        {"Close": [100 + i * 0.1 for i in range(300)]},
        index=pd.bdate_range("2022-01-01", periods=300),
    )

    monkeypatch.setattr("app.services.scoring.fetch_macro", lambda db, force=False: {"regime": {}, "themes": {}})
    monkeypatch.setattr(
        "app.services.scoring.fetch_sentiment",
        lambda db, force=False: {"themes": {}},
    )
    monkeypatch.setattr("app.services.scoring.fetch_history", lambda t, p, db: hist)
    monkeypatch.setattr(
        "app.services.scoring.fetch_fundamentals",
        lambda t, db: {"expense_ratio": 0.05, "dividend_yield": 0.02},
    )
    monkeypatch.setattr("app.services.scoring.macro_fit_score", lambda *a, **k: 50.0)
    monkeypatch.setattr(
        "app.services.scoring.sentiment_adjustment",
        lambda *a, **k: (50.0, ""),
    )

    response = run_recommendations(db, onboarded_profile)
    assert response.run_id is not None
    assert isinstance(response.recommendations, list)
