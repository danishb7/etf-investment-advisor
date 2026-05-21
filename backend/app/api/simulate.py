from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ForwardSimRequest, ForwardSimResponse, HistoricalSimRequest, HistoricalSimResponse
from app.services.simulator import forward_simulation, historical_simulation

router = APIRouter(prefix="/api/simulate", tags=["simulate"])


@router.post("/historical", response_model=HistoricalSimResponse)
def simulate_historical(body: HistoricalSimRequest, db: Session = Depends(get_db)):
    try:
        return historical_simulation(body.ticker, body.amount, body.start_date, db)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/forward", response_model=ForwardSimResponse)
def simulate_forward(body: ForwardSimRequest, db: Session = Depends(get_db)):
    try:
        return forward_simulation(body, db)
    except ValueError as e:
        raise HTTPException(400, str(e))
