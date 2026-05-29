from app.models.models import InvestorProfile
from app.services.scoring import ESG_BOOST, SHARIAH_BOOST, _apply_preference_boosts


def test_esg_boost_when_preference_on():
    profile = InvestorProfile(esg_preference=True)
    etf = {"ticker": "ESGV", "esg": True, "category": "broad_equity"}
    score, esg_fit, shariah_fit = _apply_preference_boosts(70.0, etf, profile)
    assert score == 70.0 + ESG_BOOST
    assert esg_fit == float(ESG_BOOST)
    assert shariah_fit == 0.0


def test_no_esg_boost_without_preference():
    profile = InvestorProfile(esg_preference=False)
    etf = {"ticker": "ESGV", "esg": True, "category": "broad_equity"}
    score, esg_fit, _ = _apply_preference_boosts(70.0, etf, profile)
    assert score == 70.0
    assert esg_fit == 0.0


def test_shariah_boost_always():
    profile = InvestorProfile(esg_preference=False)
    etf = {"ticker": "SPUS", "esg": False, "shariah": True, "category": "shariah"}
    score, esg_fit, shariah_fit = _apply_preference_boosts(70.0, etf, profile)
    assert score == 70.0 + SHARIAH_BOOST
    assert shariah_fit == float(SHARIAH_BOOST)
    assert esg_fit == 0.0


def test_stacked_esg_and_shariah_capped_at_100():
    profile = InvestorProfile(esg_preference=True)
    etf = {"ticker": "X", "esg": True, "shariah": True, "category": "shariah"}
    score, _, _ = _apply_preference_boosts(95.0, etf, profile)
    assert score == 100.0
