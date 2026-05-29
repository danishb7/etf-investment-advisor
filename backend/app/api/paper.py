import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import PaperPosition
from app.schemas import PaperPositionCreate, PaperPositionResponse
from app.services.market_data import fetch_history, fetch_quote

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/paper-positions", tags=["paper"])


@router.get("", response_model=list[PaperPositionResponse])
def list_positions(db: Session = Depends(get_db)):
    positions = db.query(PaperPosition).all()
    result = []
    for p in positions:
        quote = fetch_quote(p.ticker, db)
        price = quote.get("price")
        current_value = price * p.shares if price else None
        gain = (current_value - p.amount_invested) if current_value else None
        gain_pct = (gain / p.amount_invested * 100) if gain and p.amount_invested else None
        spark = []
        try:
            hist = fetch_history(p.ticker, "3m", db)
            if not hist.empty:
                spark = hist["Close"].astype(float).tail(30).tolist()
        except Exception as exc:
            logger.warning("paper sparkline failed ticker=%s: %s", p.ticker, exc)
        result.append(
            PaperPositionResponse(
                id=p.id,
                ticker=p.ticker,
                amount_invested=p.amount_invested,
                shares=p.shares,
                purchase_date=p.purchase_date,
                current_price=price,
                current_value=round(current_value, 2) if current_value else None,
                gain_loss=round(gain, 2) if gain is not None else None,
                gain_loss_pct=round(gain_pct, 2) if gain_pct is not None else None,
                sparkline=spark,
            )
        )
    return result


@router.post("", response_model=PaperPositionResponse)
def create_position(body: PaperPositionCreate, db: Session = Depends(get_db)):
    purchase_date = body.purchase_date or datetime.utcnow().strftime("%Y-%m-%d")
    quote = fetch_quote(body.ticker.upper(), db)
    price = quote.get("price")
    if not price:
        raise HTTPException(400, f"Could not fetch price for {body.ticker}")
    shares = body.amount_invested / price
    pos = PaperPosition(
        ticker=body.ticker.upper(),
        amount_invested=body.amount_invested,
        shares=shares,
        purchase_date=purchase_date,
    )
    db.add(pos)
    db.commit()
    db.refresh(pos)
    return list_positions(db)[-1]


@router.delete("/{position_id}")
def delete_position(position_id: int, db: Session = Depends(get_db)):
    pos = db.query(PaperPosition).filter(PaperPosition.id == position_id).first()
    if not pos:
        raise HTTPException(404, "Position not found")
    db.delete(pos)
    db.commit()
    return {"deleted": position_id}
