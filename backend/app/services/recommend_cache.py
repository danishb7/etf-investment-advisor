import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import InvestorProfile, RecommendationRun
from app.schemas import RecommendResponse

logger = logging.getLogger(__name__)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_cached_recommendation(
    db: Session, profile: InvestorProfile, force: bool = False
) -> RecommendResponse | None:
    if force:
        return None

    run = (
        db.query(RecommendationRun)
        .order_by(RecommendationRun.created_at.desc())
        .first()
    )
    if not run:
        return None

    now = datetime.now(timezone.utc)
    run_at = _as_utc(run.created_at)
    age = now - run_at
    if age > timedelta(minutes=settings.recommendation_ttl_minutes):
        logger.info("recommend cache MISS reason=ttl_expired age_min=%.1f", age.total_seconds() / 60)
        return None

    if profile.updated_at:
        profile_at = _as_utc(profile.updated_at)
        if profile_at > run_at:
            logger.info("recommend cache MISS reason=profile_updated")
            return None

    try:
        response = RecommendResponse.model_validate_json(run.result_json)
    except Exception as exc:
        logger.warning("recommend cache MISS reason=invalid_json error=%s", exc)
        return None

    response.cached = True
    response.generated_at = run_at
    response.run_id = run.id
    logger.info(
        "recommend cache HIT run_id=%s age_min=%.1f",
        run.id,
        age.total_seconds() / 60,
    )
    return response
