def test_paper_positions(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.paper.fetch_quote",
        lambda ticker, db: {"ticker": ticker, "price": 100.0, "as_of": "2024-01-01"},
    )
    monkeypatch.setattr(
        "app.api.paper.fetch_history",
        lambda ticker, period, db: __import__("pandas").DataFrame(),
    )

    r = client.post("/api/paper-positions", json={"ticker": "VTI", "amount_invested": 1000})
    assert r.status_code == 200
    pos_id = r.json()["id"]

    r = client.get("/api/paper-positions")
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.delete(f"/api/paper-positions/{pos_id}")
    assert r.status_code == 200
