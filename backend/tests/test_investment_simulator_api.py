def test_investment_simulator_crud(client, monkeypatch):
    from app.services.investment_simulator import run_investment_backtest

    def fake_backtest(db, **kwargs):
        return {
            "start_date": kwargs["start_date"],
            "end_date": kwargs["end_date"],
            "total_invested": 1000,
            "final_value": 1100,
            "return_pct": 10,
            "max_drawdown": -5,
            "series": [],
            "contributions": [],
            "holdings": [],
        }

    monkeypatch.setattr("app.api.investment_simulator.run_investment_backtest", fake_backtest)

    body = {
        "name": "Test plan",
        "start_date": "2020-01-01",
        "lump_sum": 1000,
        "monthly_amount": 0,
        "contribution_day": 1,
        "legs": [{"ticker": "VTI", "allocation_pct": 100}],
    }
    r = client.post("/api/investment-simulator", json=body)
    assert r.status_code == 200
    sid = r.json()["id"]

    r = client.get(f"/api/investment-simulator/{sid}")
    assert r.status_code == 200

    r = client.put(f"/api/investment-simulator/{sid}", json={"name": "Renamed"})
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed"

    r = client.post(f"/api/investment-simulator/{sid}/run")
    assert r.status_code == 200

    r = client.delete(f"/api/investment-simulator/{sid}")
    assert r.status_code == 200
