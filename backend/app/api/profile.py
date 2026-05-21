from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import InvestorProfile
from app.schemas import ProfileResponse, ProfileUpdate

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _get_or_create(db: Session) -> InvestorProfile:
    profile = db.query(InvestorProfile).first()
    if not profile:
        profile = InvestorProfile()
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("", response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db)):
    p = _get_or_create(db)
    return ProfileResponse(
        id=p.id,
        lump_sum=p.lump_sum,
        monthly_sip=p.monthly_sip,
        horizon_months=p.horizon_months,
        risk_tolerance=p.risk_tolerance,
        goal=p.goal,
        tax_bracket=p.tax_bracket,
        max_expense_ratio=p.max_expense_ratio,
        exclude_sectors=p.exclude_sectors,
        esg_preference=p.esg_preference,
        onboarding_complete=p.onboarding_complete,
        updated_at=p.updated_at,
    )


@router.put("", response_model=ProfileResponse)
def update_profile(body: ProfileUpdate, db: Session = Depends(get_db)):
    p = _get_or_create(db)
    for field, value in body.model_dump().items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return get_profile(db)
