from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.models import PortfolioHolding, WatchlistItem
from app.schemas import PortfolioHoldingCreate, PortfolioHoldingResponse, WatchlistItemSchema
from app.services.market_data import fetch_quote
from app.services.simulator import check_rebalancing, tax_loss_hints

router = APIRouter(prefix="/api", tags=["portfolio"])


@router.get("/portfolio", response_model=list[PortfolioHoldingResponse])
def list_holdings(db: Session = Depends(get_db)):
    holdings = db.query(PortfolioHolding).all()
    result = []
    for h in holdings:
        quote = fetch_quote(h.ticker, db)
        price = quote.get("price")
        current_value = price * h.shares if price else None
        gain = None
        gain_pct = None
        if current_value and h.cost_basis:
            gain = current_value - h.cost_basis
            gain_pct = gain / h.cost_basis * 100
        result.append(
            PortfolioHoldingResponse(
                id=h.id,
                ticker=h.ticker,
                shares=h.shares,
                cost_basis=h.cost_basis,
                purchase_date=h.purchase_date,
                current_price=price,
                current_value=round(current_value, 2) if current_value else None,
                gain_loss=round(gain, 2) if gain is not None else None,
                gain_loss_pct=round(gain_pct, 2) if gain_pct is not None else None,
            )
        )
    return result


@router.post("/portfolio", response_model=PortfolioHoldingResponse)
def add_holding(body: PortfolioHoldingCreate, db: Session = Depends(get_db)):
    h = PortfolioHolding(
        ticker=body.ticker.upper(),
        shares=body.shares,
        cost_basis=body.cost_basis,
        purchase_date=body.purchase_date,
    )
    db.add(h)
    db.commit()
    db.refresh(h)
    return list_holdings(db)[-1]


@router.delete("/portfolio/{holding_id}")
def delete_holding(holding_id: int, db: Session = Depends(get_db)):
    h = db.query(PortfolioHolding).filter(PortfolioHolding.id == holding_id).first()
    if not h:
        raise HTTPException(404, "Holding not found")
    db.delete(h)
    db.commit()
    return {"deleted": holding_id}


@router.get("/portfolio/rebalance")
def rebalance_alerts(db: Session = Depends(get_db)):
    return check_rebalancing(db, settings.rebalance_drift_threshold)


@router.get("/portfolio/tax-hints")
def tax_hints(db: Session = Depends(get_db)):
    return tax_loss_hints(db)


@router.get("/watchlist")
def get_watchlist(db: Session = Depends(get_db)):
    return {"items": [w.ticker for w in db.query(WatchlistItem).all()]}


@router.post("/watchlist")
def add_watchlist(body: WatchlistItemSchema, db: Session = Depends(get_db)):
    existing = db.query(WatchlistItem).filter(WatchlistItem.ticker == body.ticker.upper()).first()
    if not existing:
        db.add(WatchlistItem(ticker=body.ticker.upper()))
        db.commit()
    return {"ticker": body.ticker.upper()}


@router.delete("/watchlist/{ticker}")
def remove_watchlist(ticker: str, db: Session = Depends(get_db)):
    w = db.query(WatchlistItem).filter(WatchlistItem.ticker == ticker.upper()).first()
    if w:
        db.delete(w)
        db.commit()
    return {"deleted": ticker.upper()}
