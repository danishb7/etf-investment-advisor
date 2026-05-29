import json
import logging
from datetime import datetime, timedelta

import feedparser
from sqlalchemy.orm import Session
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.models.models import SentimentCache

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    ("rates", "https://www.federalreserve.gov/feeds/press_all.xml"),
    ("macro", "https://feeds.reuters.com/reuters/businessNews"),
    ("markets", "https://feeds.reuters.com/reuters/marketsNews"),
]

THEME_KEYWORDS = {
    "rates": ["rate", "fed", "treasury", "yield", "interest", "fomc"],
    "inflation": ["inflation", "cpi", "prices", "pce"],
    "tech": ["tech", "ai", "semiconductor", "software", "nasdaq"],
    "energy": ["oil", "energy", "opec", "gas"],
    "geopolitics": ["war", "sanction", "china", "trade", "geopolit"],
}

SECTOR_THEME_MAP = {
    "technology": "tech",
    "semiconductors": "tech",
    "innovation": "tech",
    "energy": "energy",
    "long_duration": "rates",
    "short_duration": "rates",
    "inflation_protected": "inflation",
    "aggregate_bonds": "rates",
    "corporate_bonds": "rates",
    "gold": "inflation",
    "growth": "tech",
    "shariah_us": "markets",
}

analyzer = SentimentIntensityAnalyzer()


def fetch_sentiment(db: Session, force: bool = False) -> dict:
    cached = db.query(SentimentCache).first()
    if cached and not force:
        age = datetime.utcnow() - cached.fetched_at
        if age < timedelta(hours=6):
            return json.loads(cached.data_json)

    headlines: list[dict] = []
    theme_scores: dict[str, list[float]] = {k: [] for k in THEME_KEYWORDS}

    for feed_theme, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                title = entry.get("title", "")
                summary = entry.get("summary", title)
                text = f"{title}. {summary}"[:500]
                vs = analyzer.polarity_scores(text)
                compound = vs["compound"]

                matched_themes = []
                lower = text.lower()
                for theme, keywords in THEME_KEYWORDS.items():
                    if any(kw in lower for kw in keywords):
                        theme_scores[theme].append(compound)
                        matched_themes.append(theme)
                if not matched_themes:
                    theme_scores.setdefault(feed_theme, []).append(compound)

                headlines.append({
                    "title": title[:200],
                    "source": url,
                    "themes": matched_themes or [feed_theme],
                    "compound": round(compound, 3),
                    "published": entry.get("published", ""),
                })
        except Exception as exc:
            logger.warning("sentiment feed failed url=%s: %s", url, exc)
            continue

    themes_result = {}
    for theme, scores in theme_scores.items():
        if scores:
            avg = sum(scores) / len(scores)
            themes_result[theme] = {
                "score": round(avg, 3),
                "label": "bullish" if avg > 0.1 else "bearish" if avg < -0.1 else "neutral",
                "headline_count": len(scores),
            }

    result = {
        "themes": themes_result,
        "headlines": headlines[:20],
        "fetched_at": datetime.utcnow().isoformat(),
    }

    _save_sentiment(db, result)
    return result


def _save_sentiment(db: Session, data: dict) -> None:
    cached = db.query(SentimentCache).first()
    payload = json.dumps(data)
    if cached:
        cached.data_json = payload
        cached.fetched_at = datetime.utcnow()
    else:
        db.add(SentimentCache(data_json=payload))
    db.commit()


def sentiment_adjustment(sector: str, themes: dict) -> tuple[float, str]:
    theme_key = SECTOR_THEME_MAP.get(sector)
    if not theme_key or theme_key not in themes:
        return 50.0, ""

    t = themes[theme_key]
    score = 50 + t["score"] * 50
    label = f"Sentiment: {t['label']} {theme_key}"
    return max(0, min(100, score)), label
