import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd

from app.config import settings
from app.models.models import MacroCache
from app.services.fred import fetch_macro


@patch("fredapi.Fred")
def test_refetches_stale_unavailable_cache_when_key_set(mock_fred_cls, db, monkeypatch):
    monkeypatch.setattr(settings, "fred_api_key", "0123456789abcdef0123456789abcdef")

    db.add(
        MacroCache(
            data_json=json.dumps(
                {
                    "series": {},
                    "regime": {},
                    "available": False,
                    "message": "FRED_API_KEY not set — macro overlay uses neutral defaults",
                }
            ),
            fetched_at=datetime.utcnow(),
        )
    )
    db.commit()

    idx = pd.bdate_range("2024-01-01", periods=10)
    series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0], index=idx)
    mock_fred_cls.return_value.get_series.return_value = series

    result = fetch_macro(db, force=False)

    assert result["available"] is True
    assert "fed_funds" in result["series"]
    assert mock_fred_cls.return_value.get_series.call_count == 5
