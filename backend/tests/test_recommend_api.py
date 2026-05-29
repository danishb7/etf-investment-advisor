import json
from datetime import datetime, timedelta, timezone

from app.models.models import InvestorProfile, RecommendationRun


def _onboard(client):
    client.put(
        "/api/profile",
        json={
            "lump_sum": 5000,
            "monthly_sip": 200,
            "horizon_months": 60,
            "risk_tolerance": "balanced",
            "goal": "wealth_building",
            "onboarding_complete": True,
        },
    )


def test_get_recommend_requires_onboarding(client):
    r = client.get("/api/recommend")
    assert r.status_code == 400


def test_post_recommend_generates_run(client, db, monkeypatch):
    _onboard(client)

    def fake_run(db_sess, profile):
        from app.schemas import RecommendResponse

        return RecommendResponse(
            recommendations=[],
            near_misses=[],
            portfolio_warnings=[],
            weighted_expense_ratio=None,
            estimated_volatility=None,
            sector_exposure={},
            run_id=None,
            cached=False,
        )

    monkeypatch.setattr("app.api.recommend.run_recommendations", fake_run)
    r = client.post("/api/recommend")
    assert r.status_code == 200
    assert r.json()["cached"] is False


def test_get_recommend_returns_cache(client, db):
    _onboard(client)
    profile = db.query(InvestorProfile).first()
    payload = {
        "recommendations": [],
        "near_misses": [],
        "portfolio_warnings": [],
        "weighted_expense_ratio": None,
        "estimated_volatility": None,
        "sector_exposure": {},
        "run_id": None,
        "cached": False,
        "generated_at": None,
    }
    run = RecommendationRun(result_json=json.dumps(payload))
    db.add(run)
    db.commit()
    profile.updated_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db.commit()

    r = client.get("/api/recommend")
    assert r.status_code == 200
    assert r.json()["cached"] is True


def test_get_recommend_regenerates_when_profile_newer(client, db, monkeypatch):
    _onboard(client)
    profile = db.query(InvestorProfile).first()
    old_payload = {
        "recommendations": [],
        "near_misses": [],
        "portfolio_warnings": [],
        "weighted_expense_ratio": None,
        "estimated_volatility": None,
        "sector_exposure": {},
    }
    run = RecommendationRun(
        result_json=json.dumps(old_payload),
        created_at=datetime.utcnow() - timedelta(minutes=5),
    )
    db.add(run)
    db.commit()
    profile.updated_at = datetime.utcnow()
    db.commit()

    calls = {"n": 0}

    def fake_run(db_sess, prof):
        calls["n"] += 1
        from app.schemas import RecommendResponse

        return RecommendResponse(
            recommendations=[],
            near_misses=[],
            portfolio_warnings=[],
            weighted_expense_ratio=None,
            estimated_volatility=None,
            sector_exposure={},
        )

    monkeypatch.setattr("app.api.recommend.run_recommendations", fake_run)
    r = client.get("/api/recommend")
    assert r.status_code == 200
    assert calls["n"] == 1
    assert r.json()["cached"] is False
