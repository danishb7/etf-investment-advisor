import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import MacroCache

FRED_SERIES = {
    "fed_funds": "FEDFUNDS",
    "cpi": "CPIAUCSL",
    "unemployment": "UNRATE",
    "ten_year_yield": "DGS10",
    "two_year_yield": "DGS2",
}


def fetch_macro(db: Session, force: bool = False) -> dict:
    cached = db.query(MacroCache).first()
    if cached and not force:
        age = datetime.utcnow() - cached.fetched_at
        if age < timedelta(hours=24):
            payload = json.loads(cached.data_json)
            # Refetch if a key is now set but cache still has pre-key "unavailable" snapshot.
            if payload.get("available") or not settings.fred_api_key.strip():
                return payload

    result = {"series": {}, "regime": {}, "fetched_at": datetime.utcnow().isoformat(), "available": False}

    if not settings.fred_api_key:
        result["message"] = "FRED_API_KEY not set — macro overlay uses neutral defaults"
        _save_macro(db, result)
        return result

    try:
        from fredapi import Fred

        fred = Fred(api_key=settings.fred_api_key)
        for key, series_id in FRED_SERIES.items():
            try:
                s = fred.get_series(series_id, observation_start="2020-01-01")
                if s is not None and len(s) > 0:
                    latest = float(s.dropna().iloc[-1])
                    prev = float(s.dropna().iloc[-2]) if len(s.dropna()) > 1 else latest
                    result["series"][key] = {
                        "value": latest,
                        "change": latest - prev,
                        "series_id": series_id,
                    }
            except Exception as exc:
                logger.warning("FRED series %s (%s) failed: %s", key, series_id, exc)
                continue

        result["available"] = len(result["series"]) > 0
        if not result["available"] and settings.fred_api_key.strip():
            result["message"] = "FRED API key set but no series returned — check key and network"
        result["regime"] = _infer_regime(result["series"])
        _save_macro(db, result)
    except Exception as e:
        result["message"] = str(e)
        _save_macro(db, result)

    return result


def _save_macro(db: Session, data: dict) -> None:
    cached = db.query(MacroCache).first()
    payload = json.dumps(data)
    if cached:
        cached.data_json = payload
        cached.fetched_at = datetime.utcnow()
    else:
        db.add(MacroCache(data_json=payload))
    db.commit()


def _infer_regime(series: dict) -> dict:
    regime = {"rates": "neutral", "inflation": "neutral", "growth": "neutral"}
    ff = series.get("fed_funds", {})
    cpi = series.get("cpi", {})
    unemp = series.get("unemployment", {})
    y10 = series.get("ten_year_yield", {})
    y2 = series.get("two_year_yield", {})

    if y10.get("value") and y2.get("value"):
        spread = y10["value"] - y2["value"]
        regime["rates"] = "rising" if spread < 0 else "falling" if spread > 1.5 else "neutral"

    if cpi.get("change") and cpi["change"] > 0.3:
        regime["inflation"] = "elevated"
    elif cpi.get("change") and cpi["change"] < 0:
        regime["inflation"] = "low"

    if unemp.get("change"):
        regime["growth"] = "weakening" if unemp["change"] > 0.1 else "stable"

    if ff.get("change") and ff["change"] > 0.05:
        regime["rates"] = "rising"

    return regime


def macro_fit_score(sector: str, category: str, regime: dict) -> float:
    score = 50.0
    rates = regime.get("rates", "neutral")
    inflation = regime.get("inflation", "neutral")

    if category == "bonds":
        if sector == "long_duration" and rates == "rising":
            score -= 20
        elif sector == "short_duration" and rates == "rising":
            score += 15
        elif sector == "inflation_protected" and inflation == "elevated":
            score += 20
    elif category in ("broad_equity", "growth", "shariah") and rates == "rising":
        score -= 5
    elif category == "commodity" and sector == "gold" and inflation == "elevated":
        score += 15
    elif category == "cash" and rates == "rising":
        score += 10

    return max(0, min(100, score))
