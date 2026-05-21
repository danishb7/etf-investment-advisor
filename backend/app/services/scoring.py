import json
from datetime import datetime

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import InvestorProfile, LastRecommendation, RecommendationRun
from app.schemas import ETFRecommendation, RecommendResponse, ScoreBreakdown
from app.services.fred import fetch_macro, macro_fit_score
from app.services.market_data import compute_stats, fetch_fundamentals, fetch_history
from app.services.sentiment import fetch_sentiment, sentiment_adjustment
from app.services.universe import load_universe

RISK_VOL_CAP = {"conservative": 12, "balanced": 18, "aggressive": 28}
CORRELATION_THRESHOLD = 0.92


def _momentum_score(hist: pd.DataFrame, horizon_months: int) -> float:
    if hist.empty or len(hist) < 30:
        return 50.0
    closes = hist["Close"].astype(float)
    scores = []
    windows = [(63, 0.25), (126, 0.35), (252, 0.4)]
    if horizon_months < 12:
        windows = [(21, 0.4), (63, 0.35), (126, 0.25)]
    for days, weight in windows:
        if len(closes) > days:
            ret = (closes.iloc[-1] / closes.iloc[-days] - 1) * 100
            normalized = max(0, min(100, 50 + ret * 2))
            scores.append(normalized * weight)
    return sum(scores) if scores else 50.0


def _sharpe_score(stats: dict) -> float:
    sharpe = stats.get("sharpe_ratio", 0) or 0
    return max(0, min(100, 50 + sharpe * 25))


def _volatility_score(stats: dict, risk: str) -> float:
    vol = stats.get("volatility", 15) or 15
    cap = RISK_VOL_CAP.get(risk, 18)
    if vol <= cap * 0.5:
        return 90
    if vol <= cap:
        return 70
    if vol <= cap * 1.5:
        return 40
    return 15


def _expense_score(expense: float | None, max_er: float) -> float:
    if expense is None:
        return 60.0
    er_pct = expense * 100 if expense < 1 else expense
    if er_pct > max_er:
        return 10.0
    return max(0, min(100, 100 - er_pct * 40))


def _dividend_score(div_yield: float | None, goal: str) -> float:
    if goal not in ("income", "retirement") or div_yield is None:
        return 50.0
    dy = div_yield * 100 if div_yield < 1 else div_yield
    return max(0, min(100, 40 + dy * 15))


def _build_explanation(breakdown: ScoreBreakdown, etf: dict, sentiment_label: str) -> str:
    parts = [
        f"{etf['name']} ({etf['ticker']}) fits your {etf['category'].replace('_', ' ')} allocation.",
        f"Strong momentum ({breakdown.momentum:.0f}/100)" if breakdown.momentum >= 65 else f"Moderate momentum ({breakdown.momentum:.0f}/100)",
        f"risk-adjusted returns score {breakdown.sharpe:.0f}/100",
        f"expense score {breakdown.expense:.0f}/100",
    ]
    if sentiment_label:
        parts.append(sentiment_label)
    return " ".join(parts) + "."


def _risk_warning(etf: dict, stats: dict, breakdown: ScoreBreakdown) -> str | None:
    warnings = []
    if stats.get("max_drawdown", 0) and stats["max_drawdown"] < -25:
        warnings.append(f"Historical max drawdown {stats['max_drawdown']:.1f}%")
    if etf["category"] == "sector":
        warnings.append("Single-sector concentration risk")
    if etf["sector"] == "long_duration":
        warnings.append("Sensitive to interest rate changes")
    if breakdown.volatility < 40:
        warnings.append("Volatility may exceed your risk profile")
    return "; ".join(warnings) if warnings else None


def _correlation_filter(candidates: list[dict], price_data: dict[str, pd.DataFrame]) -> list[dict]:
    selected: list[dict] = []
    for c in candidates:
        ticker = c["ticker"]
        if ticker not in price_data or price_data[ticker].empty:
            selected.append(c)
            continue
        too_correlated = False
        ret_a = price_data[ticker]["Close"].astype(float).pct_change().dropna()
        for s in selected:
            if s["ticker"] not in price_data:
                continue
            ret_b = price_data[s["ticker"]]["Close"].astype(float).pct_change().dropna()
            aligned = pd.concat([ret_a, ret_b], axis=1).dropna()
            if len(aligned) < 30:
                continue
            corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
            if corr and corr > CORRELATION_THRESHOLD:
                too_correlated = True
                c["_correlation_note"] = f"Highly correlated with {s['ticker']} ({corr:.2f})"
                break
        if not too_correlated:
            selected.append(c)
    return selected


def _allocate(top: list[dict], profile: InvestorProfile) -> list[dict]:
    if not top:
        return []
    risk = profile.risk_tolerance
    n = min(len(top), 8 if risk == "aggressive" else 6 if risk == "balanced" else 5)
    picks = top[:n]
    weights = []
    for i, p in enumerate(picks):
        base = p["final_score"]
        w = base ** 1.5
        weights.append(w)
    total = sum(weights) or 1
    for p, w in zip(picks, weights):
        p["allocation_pct"] = round(w / total * 100, 1)
    drift = 100 - sum(p["allocation_pct"] for p in picks)
    if picks and drift:
        picks[0]["allocation_pct"] = round(picks[0]["allocation_pct"] + drift, 1)
    return picks


def run_recommendations(db: Session, profile: InvestorProfile) -> RecommendResponse:
    macro = fetch_macro(db)
    sentiment_data = fetch_sentiment(db)
    themes = sentiment_data.get("themes", {})
    regime = macro.get("regime", {})

    exclude = {s.strip().lower() for s in profile.exclude_sectors.split(",") if s.strip()}
    universe = [e for e in load_universe() if e["sector"].lower() not in exclude]

    scored: list[dict] = []
    price_data: dict[str, pd.DataFrame] = {}

    for etf in universe:
        ticker = etf["ticker"]
        try:
            hist = fetch_history(ticker, "1y", db)
            price_data[ticker] = hist
            stats = compute_stats(hist)
            fund = fetch_fundamentals(ticker, db)

            expense = fund.get("expense_ratio")
            if expense and expense > profile.max_expense_ratio / 100 * 2:
                continue

            mom = _momentum_score(hist, profile.horizon_months)
            sharpe = _sharpe_score(stats)
            vol = _volatility_score(stats, profile.risk_tolerance)
            exp = _expense_score(expense, profile.max_expense_ratio)
            div = _dividend_score(fund.get("dividend_yield"), profile.goal)
            macro_s = macro_fit_score(etf["sector"], etf["category"], regime)
            sent_s, sent_label = sentiment_adjustment(etf["sector"], themes)

            rule_score = (
                mom * 0.28
                + sharpe * 0.22
                + vol * 0.2
                + exp * 0.15
                + div * 0.05
                + macro_s * 0.1
            )
            final_score = rule_score * 0.92 + sent_s * 0.08

            if settings.ml_enabled:
                from app.services.ml import get_ml_score

                ml_s = get_ml_score(etf, stats, macro)
                final_score = rule_score * 0.7 + ml_s * 0.3

            scored.append({
                **etf,
                "rule_score": round(rule_score, 2),
                "final_score": round(final_score, 2),
                "breakdown": {
                    "momentum": round(mom, 1),
                    "sharpe": round(sharpe, 1),
                    "volatility": round(vol, 1),
                    "expense": round(exp, 1),
                    "dividend": round(div, 1),
                    "macro_fit": round(macro_s, 1),
                    "sentiment": round(sent_s, 1),
                },
                "stats": stats,
                "fund": fund,
                "sentiment_label": sent_label,
            })
        except Exception:
            continue

    scored.sort(key=lambda x: x["final_score"], reverse=True)
    filtered = _correlation_filter(scored, price_data)
    top = _allocate(filtered, profile)
    near_misses = [s for s in scored if s["ticker"] not in {t["ticker"] for t in top}][:3]

    recommendations = []
    for s in top:
        bd = ScoreBreakdown(**s["breakdown"])
        recommendations.append(
            ETFRecommendation(
                ticker=s["ticker"],
                name=s["name"],
                category=s["category"],
                sector=s["sector"],
                final_score=s["final_score"],
                rule_score=s["rule_score"],
                allocation_pct=s.get("allocation_pct", 0),
                breakdown=bd,
                expense_ratio=s["fund"].get("expense_ratio"),
                return_1y=s["stats"].get("return_pct"),
                max_drawdown=s["stats"].get("max_drawdown"),
                sharpe_ratio=s["stats"].get("sharpe_ratio"),
                explanation=_build_explanation(bd, s, s.get("sentiment_label", "")),
                risk_warning=_risk_warning(s, s["stats"], bd),
            )
        )

    nm_list = []
    for s in near_misses:
        bd = ScoreBreakdown(**s["breakdown"])
        nm_list.append(
            ETFRecommendation(
                ticker=s["ticker"],
                name=s["name"],
                category=s["category"],
                sector=s["sector"],
                final_score=s["final_score"],
                rule_score=s["rule_score"],
                allocation_pct=0,
                breakdown=bd,
                expense_ratio=s["fund"].get("expense_ratio"),
                return_1y=s["stats"].get("return_pct"),
                max_drawdown=s["stats"].get("max_drawdown"),
                sharpe_ratio=s["stats"].get("sharpe_ratio"),
                explanation=_build_explanation(bd, s, ""),
                risk_warning=_risk_warning(s, s["stats"], bd),
            )
        )

    sector_exp: dict[str, float] = {}
    total_alloc = sum(r.allocation_pct for r in recommendations) or 1
    for r in recommendations:
        sector_exp[r.sector] = sector_exp.get(r.sector, 0) + r.allocation_pct / total_alloc * 100

    warnings = []
    if any(r.allocation_pct > 35 for r in recommendations):
        warnings.append("One holding exceeds 35% — consider diversifying further")
    if sector_exp and max(sector_exp.values()) > 50:
        warnings.append("Portfolio is concentrated in a single sector")

    er_weighted = None
    ers = [(r.expense_ratio or 0) * r.allocation_pct for r in recommendations if r.expense_ratio]
    if ers:
        er_weighted = round(sum(ers) / total_alloc / 100, 4)

    vols = [s["stats"].get("volatility") for s in top if s.get("stats", {}).get("volatility")]
    est_vol = round(sum(vols) / len(vols), 2) if vols else None

    response = RecommendResponse(
        recommendations=recommendations,
        near_misses=nm_list,
        portfolio_warnings=warnings,
        weighted_expense_ratio=er_weighted,
        estimated_volatility=est_vol,
        sector_exposure={k: round(v, 1) for k, v in sector_exp.items()},
    )

    run = RecommendationRun(
        result_json=response.model_dump_json(),
        macro_snapshot=json.dumps(macro.get("regime", {})),
    )
    db.add(run)
    db.commit()
    response.run_id = run.id

    alloc_map = {r.ticker: r.allocation_pct for r in recommendations}
    last = db.query(LastRecommendation).first()
    if last:
        last.allocations_json = json.dumps(alloc_map)
    else:
        db.add(LastRecommendation(allocations_json=json.dumps(alloc_map)))
    db.commit()

    return response
