from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import InvestorProfile
from app.schemas import RecommendResponse
from app.services.recommend_cache import get_cached_recommendation
from app.services.scoring import run_recommendations

router = APIRouter(prefix="/api", tags=["recommend"])


def _require_onboarded_profile(db: Session) -> InvestorProfile:
    profile = db.query(InvestorProfile).first()
    if not profile or not profile.onboarding_complete:
        raise HTTPException(400, "Complete onboarding before requesting recommendations")
    return profile


@router.get("/recommend", response_model=RecommendResponse)
def get_recommend(
    force: bool = Query(False),
    db: Session = Depends(get_db),
):
    profile = _require_onboarded_profile(db)
    cached = get_cached_recommendation(db, profile, force=force)
    if cached:
        return cached
    response = run_recommendations(db, profile)
    response.cached = False
    response.generated_at = datetime.now(timezone.utc)
    return response


@router.post("/recommend", response_model=RecommendResponse)
def refresh_recommend(db: Session = Depends(get_db)):
    profile = _require_onboarded_profile(db)
    response = run_recommendations(db, profile)
    response.cached = False
    response.generated_at = datetime.now(timezone.utc)
    return response


@router.get("/recommend/history")
def recommend_history(limit: int = 10, db: Session = Depends(get_db)):
    import json

    from app.models.models import RecommendationRun

    runs = db.query(RecommendationRun).order_by(RecommendationRun.created_at.desc()).limit(limit).all()
    return {
        "runs": [
            {
                "id": r.id,
                "created_at": r.created_at.isoformat(),
                "preview": json.loads(r.result_json).get("recommendations", [])[:3],
            }
            for r in runs
        ]
    }
