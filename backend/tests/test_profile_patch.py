def test_partial_profile_update_preserves_fields(client):
    client.put(
        "/api/profile",
        json={
            "lump_sum": 5000,
            "monthly_sip": 200,
            "horizon_months": 60,
            "risk_tolerance": "aggressive",
            "goal": "retirement",
            "onboarding_complete": True,
        },
    )
    r = client.put("/api/profile", json={"monthly_sip": 350})
    assert r.status_code == 200
    data = r.json()
    assert data["monthly_sip"] == 350
    assert data["risk_tolerance"] == "aggressive"
    assert data["lump_sum"] == 5000
