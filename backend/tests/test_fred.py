from app.services.fred import _infer_regime, macro_fit_score


def test_infer_regime_inverted_yield_curve():
    series = {
        "ten_year_yield": {"value": 3.5, "change": 0},
        "two_year_yield": {"value": 4.0, "change": 0},
    }
    regime = _infer_regime(series)
    assert regime["rates"] == "rising"


def test_macro_fit_long_duration_penalized_when_rates_rising():
    regime = {"rates": "rising", "inflation": "neutral"}
    score = macro_fit_score("long_duration", "bonds", regime)
    assert score < 50
