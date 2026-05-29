def test_historical_sim_bad_request(client, monkeypatch):
    def raise_value(*args, **kwargs):
        raise ValueError("No data after 2099-01-01")

    monkeypatch.setattr("app.api.simulate.historical_simulation", raise_value)
    r = client.post(
        "/api/simulate/historical",
        json={"ticker": "VTI", "amount": 1000, "start_date": "2099-01-01"},
    )
    assert r.status_code == 400


def test_forward_sim(client, monkeypatch):
    from app.schemas import ForwardSimResponse

    monkeypatch.setattr(
        "app.api.simulate.forward_simulation",
        lambda body, db: ForwardSimResponse(
            median_final_value=10000,
            percentile_10=8000,
            percentile_90=12000,
            series=[{"month": 0, "value": 5000}],
        ),
    )
    r = client.post(
        "/api/simulate/forward",
        json={"horizon_months": 12, "tickers": ["VTI"], "lump_sum": 1000},
    )
    assert r.status_code == 200
    assert r.json()["median_final_value"] == 10000
