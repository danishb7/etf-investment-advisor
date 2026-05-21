from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.fred import fetch_macro
from app.services.sentiment import fetch_sentiment

router = APIRouter(prefix="/api", tags=["macro-sentiment"])


@router.get("/macro")
def get_macro(force: bool = Query(False), db: Session = Depends(get_db)):
    return fetch_macro(db, force=force)


@router.get("/sentiment")
def get_sentiment(force: bool = Query(False), db: Session = Depends(get_db)):
    return fetch_sentiment(db, force=force)
