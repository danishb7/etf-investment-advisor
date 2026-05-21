import json
from pathlib import Path

_UNIVERSE_PATH = Path(__file__).parent.parent / "data" / "etf_universe.json"


def load_universe() -> list[dict]:
    with open(_UNIVERSE_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_tickers() -> list[str]:
    return [e["ticker"] for e in load_universe()]
