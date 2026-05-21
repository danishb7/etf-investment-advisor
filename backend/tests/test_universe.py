from app.services.universe import get_tickers, load_universe


def test_load_universe_has_entries():
    universe = load_universe()
    assert len(universe) >= 10
    first = universe[0]
    assert "ticker" in first
    assert "name" in first
    assert "category" in first


def test_get_tickers_matches_universe():
    tickers = get_tickers()
    assert "VTI" in tickers
    assert "SPY" in tickers
    assert len(tickers) == len(load_universe())
