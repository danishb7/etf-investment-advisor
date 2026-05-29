def test_fetch_sentiment_force(db):
    from app.services.sentiment import fetch_sentiment

    result = fetch_sentiment(db, force=True)
    assert "themes" in result
    assert "fetched_at" in result
