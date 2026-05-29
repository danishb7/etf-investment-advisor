import json
from datetime import datetime, timedelta, timezone

from app.models.models import InvestorProfile, RecommendationRun
from app.services.recommend_cache import get_cached_recommendation


def test_cache_miss_when_ttl_expired(db):
    profile = InvestorProfile(onboarding_complete=True)
    db.add(profile)
    payload = {
        "recommendations": [],
        "near_misses": [],
        "portfolio_warnings": [],
        "weighted_expense_ratio": None,
        "estimated_volatility": None,
        "sector_exposure": {},
    }
    run = RecommendationRun(
        result_json=json.dumps(payload),
        created_at=datetime.utcnow() - timedelta(hours=2),
    )
    db.add(run)
    db.commit()
    assert get_cached_recommendation(db, profile, force=False) is None
