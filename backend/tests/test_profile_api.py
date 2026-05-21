def test_get_profile_creates_default(client):
    response = client.get("/api/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["risk_tolerance"] == "balanced"
    assert data["onboarding_complete"] is False


def test_update_profile(client):
    payload = {
        "lump_sum": 5000,
        "monthly_sip": 200,
        "horizon_months": 120,
        "risk_tolerance": "aggressive",
        "goal": "retirement",
        "onboarding_complete": True,
    }
    response = client.put("/api/profile", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["lump_sum"] == 5000
    assert data["monthly_sip"] == 200
    assert data["risk_tolerance"] == "aggressive"
    assert data["onboarding_complete"] is True

    again = client.get("/api/profile")
    assert again.json()["lump_sum"] == 5000
