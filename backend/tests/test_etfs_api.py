from unittest.mock import MagicMock

import pandas as pd


def test_list_etfs_returns_static_universe(client):
    r = client.get("/api/etfs")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 10
    assert "esg" in data["etfs"][0]
    assert "ESGV" in {e["ticker"] for e in data["etfs"]}


def test_get_history_not_found(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.etfs.fetch_history",
        lambda ticker, period, db: pd.DataFrame(),
    )
    r = client.get("/api/etfs/FAKE/history?period=1y")
    assert r.status_code == 404


def test_get_quote(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.etfs.fetch_quote",
        lambda ticker, db: {"ticker": ticker, "price": 100.0, "as_of": "2024-01-01"},
    )
    r = client.get("/api/etfs/VTI/quote")
    assert r.status_code == 200
    assert r.json()["price"] == 100.0


def test_search_curated(client):
    r = client.get("/api/etfs/search?q=VTI")
    assert r.status_code == 200
    assert any(e["ticker"] == "VTI" for e in r.json()["curated"])
