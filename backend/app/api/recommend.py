from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import InvestorProfile, RecommendationRun
from app.schemas import RecommendResponse
from app.services.scoring import run_recommendations

router = APIRouter(prefix="/api", tags=["recommend"])


@router.post("/recommend", response_model=RecommendResponse)
def recommend(db: Session = Depends(get_db)):
    profile = db.query(InvestorProfile).first()
    if not profile or not profile.onboarding_complete:
        raise HTTPException(400, "Complete onboarding before requesting recommendations")
    return run_recommendations(db, profile)


@router.get("/recommend/history")
def recommend_history(limit: int = 10, db: Session = Depends(get_db)):
    import json

    runs = db.query(RecommendationRun).order_by(RecommendationRun.created_at.desc()).limit(limit).all()
    return {
        "runs": [
            {"id": r.id, "created_at": r.created_at.isoformat(), "preview": json.loads(r.result_json).get("recommendations", [])[:3]}
            for r in runs
        ]
    }
