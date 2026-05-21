"""Optional ML layer — off by default (ML_ENABLED=false)."""

from pathlib import Path

import numpy as np

MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "etf_ranker.joblib"
_model = None


def _get_model():
    global _model
    if _model is None and MODEL_PATH.exists():
        import joblib

        _model = joblib.load(MODEL_PATH)
    return _model


def get_ml_score(etf: dict, stats: dict, macro: dict) -> float:
    model = _get_model()
    if model is None:
        return _heuristic_ml(etf, stats, macro)

    features = np.array([[
        stats.get("return_pct", 0) or 0,
        stats.get("volatility", 15) or 15,
        stats.get("sharpe_ratio", 0) or 0,
        stats.get("max_drawdown", -10) or -10,
        1 if etf["category"] == "bonds" else 0,
        1 if etf["category"] == "sector" else 0,
        macro.get("regime", {}).get("rates") == "rising",
    ]]).astype(float)

    try:
        pred = model.predict(features)[0]
        if hasattr(pred, "__len__"):
            pred = pred[0]
        return max(0, min(100, float(pred)))
    except Exception:
        return _heuristic_ml(etf, stats, macro)


def _heuristic_ml(etf: dict, stats: dict, macro: dict) -> float:
    base = 50.0
    base += (stats.get("sharpe_ratio", 0) or 0) * 10
    base += (stats.get("return_pct", 0) or 0) * 0.3
    if macro.get("regime", {}).get("inflation") == "elevated" and etf["sector"] == "inflation_protected":
        base += 10
    return max(0, min(100, base))


def train_model(db) -> dict:
    """Train and save RandomForest on historical features. Run via script."""
    import joblib
    from sklearn.ensemble import RandomForestRegressor

    from app.services.market_data import compute_stats, fetch_history
    from app.services.universe import load_universe

    X, y = [], []
    for etf in load_universe():
        try:
            hist = fetch_history(etf["ticker"], "3y", db)
            if len(hist) < 252:
                continue
            stats = compute_stats(hist.iloc[:-63])
            forward = compute_stats(hist.iloc[-63:])
            X.append([
                stats.get("return_pct", 0),
                stats.get("volatility", 15),
                stats.get("sharpe_ratio", 0),
                stats.get("max_drawdown", -10),
                1 if etf["category"] == "bonds" else 0,
                1 if etf["category"] == "sector" else 0,
            ])
            y.append(forward.get("return_pct", 0) + forward.get("sharpe_ratio", 0) * 10)
        except Exception:
            continue

    if len(X) < 10:
        return {"status": "insufficient_data", "samples": len(X)}

    model = RandomForestRegressor(n_estimators=50, max_depth=6, random_state=42)
    model.fit(np.array(X), np.array(y))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    return {"status": "trained", "samples": len(X), "path": str(MODEL_PATH)}
