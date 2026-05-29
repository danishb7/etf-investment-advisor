def test_portfolio_crud_and_watchlist(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.portfolio.fetch_quote",
        lambda ticker, db: {"ticker": ticker, "price": 50.0, "as_of": "2024-01-01"},
    )

    r = client.post("/api/portfolio", json={"ticker": "VTI", "shares": 10, "cost_basis": 400})
    assert r.status_code == 200
    holding_id = r.json()["id"]

    r = client.get("/api/portfolio")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["current_value"] == 500.0

    r = client.post("/api/watchlist", json={"ticker": "SPY"})
    assert r.status_code == 200
    r = client.get("/api/watchlist")
    assert "SPY" in r.json()["items"]

    r = client.delete(f"/api/watchlist/SPY")
    assert r.status_code == 200

    r = client.delete(f"/api/portfolio/{holding_id}")
    assert r.status_code == 200


def test_rebalance_and_tax_hints(client, monkeypatch):
    monkeypatch.setattr("app.api.portfolio.check_rebalancing", lambda db, threshold: [])
    monkeypatch.setattr("app.api.portfolio.tax_loss_hints", lambda db: [])
    assert client.get("/api/portfolio/rebalance").status_code == 200
    assert client.get("/api/portfolio/tax-hints").status_code == 200
