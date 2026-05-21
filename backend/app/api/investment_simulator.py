import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import InvestmentScenario
from app.schemas import (
    InvestmentScenarioCreate,
    InvestmentScenarioResponse,
    InvestmentScenarioUpdate,
)
from app.services.investment_simulator import run_investment_backtest

router = APIRouter(prefix="/api/investment-simulator", tags=["investment-simulator"])


def _to_response(row: InvestmentScenario) -> InvestmentScenarioResponse:
    legs = json.loads(row.legs_json)
    result = json.loads(row.result_json) if row.result_json else None
    return InvestmentScenarioResponse(
        id=row.id,
        name=row.name,
        start_date=row.start_date,
        end_date=row.end_date,
        lump_sum=row.lump_sum,
        monthly_amount=row.monthly_amount,
        contribution_day=row.contribution_day,
        legs=legs,
        result=result,
        total_invested=row.total_invested,
        final_value=row.final_value,
        return_pct=row.return_pct,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=list[InvestmentScenarioResponse])
def list_scenarios(db: Session = Depends(get_db)):
    rows = db.query(InvestmentScenario).order_by(InvestmentScenario.updated_at.desc()).all()
    return [_to_response(r) for r in rows]


@router.get("/{scenario_id}", response_model=InvestmentScenarioResponse)
def get_scenario(scenario_id: int, db: Session = Depends(get_db)):
    row = db.query(InvestmentScenario).filter(InvestmentScenario.id == scenario_id).first()
    if not row:
        raise HTTPException(404, "Scenario not found")
    return _to_response(row)


@router.post("", response_model=InvestmentScenarioResponse)
def create_scenario(body: InvestmentScenarioCreate, db: Session = Depends(get_db)):
    legs = [leg.model_dump() for leg in body.legs]
    try:
        result = run_investment_backtest(
            db,
            start_date=body.start_date,
            end_date=body.end_date,
            lump_sum=body.lump_sum,
            monthly_amount=body.monthly_amount,
            contribution_day=body.contribution_day,
            legs=legs,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    row = InvestmentScenario(
        name=body.name,
        start_date=body.start_date,
        end_date=body.end_date,
        lump_sum=body.lump_sum,
        monthly_amount=body.monthly_amount,
        contribution_day=body.contribution_day,
        legs_json=json.dumps(legs),
        result_json=json.dumps(result),
        total_invested=result["total_invested"],
        final_value=result["final_value"],
        return_pct=result["return_pct"],
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_response(row)


@router.put("/{scenario_id}", response_model=InvestmentScenarioResponse)
def update_scenario(scenario_id: int, body: InvestmentScenarioUpdate, db: Session = Depends(get_db)):
    row = db.query(InvestmentScenario).filter(InvestmentScenario.id == scenario_id).first()
    if not row:
        raise HTTPException(404, "Scenario not found")

    data = body.model_dump(exclude_unset=True)
    legs = data.pop("legs", None)
    if legs is not None:
        row.legs_json = json.dumps([
            l if isinstance(l, dict) else (l.model_dump() if hasattr(l, "model_dump") else l)
            for l in legs
        ])

    for k, v in data.items():
        setattr(row, k, v)

    legs_parsed = json.loads(row.legs_json)
    try:
        result = run_investment_backtest(
            db,
            start_date=row.start_date,
            end_date=row.end_date,
            lump_sum=row.lump_sum,
            monthly_amount=row.monthly_amount,
            contribution_day=row.contribution_day,
            legs=legs_parsed,
        )
        row.result_json = json.dumps(result)
        row.total_invested = result["total_invested"]
        row.final_value = result["final_value"]
        row.return_pct = result["return_pct"]
    except ValueError as e:
        raise HTTPException(400, str(e))

    db.commit()
    db.refresh(row)
    return _to_response(row)


@router.post("/{scenario_id}/run", response_model=InvestmentScenarioResponse)
def rerun_scenario(scenario_id: int, db: Session = Depends(get_db)):
    row = db.query(InvestmentScenario).filter(InvestmentScenario.id == scenario_id).first()
    if not row:
        raise HTTPException(404, "Scenario not found")
    legs = json.loads(row.legs_json)
    try:
        result = run_investment_backtest(
            db,
            start_date=row.start_date,
            end_date=row.end_date,
            lump_sum=row.lump_sum,
            monthly_amount=row.monthly_amount,
            contribution_day=row.contribution_day,
            legs=legs,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    row.result_json = json.dumps(result)
    row.total_invested = result["total_invested"]
    row.final_value = result["final_value"]
    row.return_pct = result["return_pct"]
    db.commit()
    db.refresh(row)
    return _to_response(row)


@router.delete("/{scenario_id}")
def delete_scenario(scenario_id: int, db: Session = Depends(get_db)):
    row = db.query(InvestmentScenario).filter(InvestmentScenario.id == scenario_id).first()
    if not row:
        raise HTTPException(404, "Scenario not found")
    db.delete(row)
    db.commit()
    return {"deleted": scenario_id}
