"""One-off FRED diagnostics (does not print API key)."""
from __future__ import annotations

import sys

from app.config import settings
from app.database import SessionLocal, init_db
from app.services.fred import FRED_SERIES, fetch_macro


def main() -> int:
    key = settings.fred_api_key.strip()
    print(f"FRED_API_KEY loaded: {bool(key)} (length={len(key)})")
    if not key:
        print("FAIL: Key empty — check backend/.env and restart from backend/")
        return 1

    print("\nPer-series FRED fetch:")
    try:
        from fredapi import Fred

        fred = Fred(api_key=key)
    except Exception as e:
        print(f"FAIL: Could not init Fred client: {e}")
        return 1

    ok = 0
    for name, series_id in FRED_SERIES.items():
        try:
            s = fred.get_series(series_id, observation_start="2020-01-01")
            n = len(s.dropna()) if s is not None else 0
            latest = float(s.dropna().iloc[-1]) if n else None
            status = "OK" if n else "EMPTY"
            print(f"  {name} ({series_id}): {status}  points={n}  latest={latest}")
            if n:
                ok += 1
        except Exception as e:
            print(f"  {name} ({series_id}): ERROR  {type(e).__name__}: {e}")

    print(f"\nSeries OK: {ok}/{len(FRED_SERIES)}")

    init_db()
    db = SessionLocal()
    try:
        macro = fetch_macro(db, force=True)
        print("\nfetch_macro(force=True):")
        print(f"  available: {macro.get('available')}")
        print(f"  message: {macro.get('message', '(none)')}")
        print(f"  series keys: {list(macro.get('series', {}).keys())}")
        print(f"  regime: {macro.get('regime')}")
    finally:
        db.close()

    return 0 if macro.get("available") else 2


if __name__ == "__main__":
    sys.exit(main())
