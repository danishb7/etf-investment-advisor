"""Run: python -m scripts.train_ml (from backend directory)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, init_db
from app.services.ml import train_model

if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    result = train_model(db)
    print(result)
    db.close()
