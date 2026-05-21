from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import etfs, investment_simulator, macro_sentiment, paper, portfolio, profile, recommend, simulate
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="ETF Investment Advisor",
    description="Educational ETF advisor — not financial advice",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router)
app.include_router(etfs.router)
app.include_router(recommend.router)
app.include_router(macro_sentiment.router)
app.include_router(paper.router)
app.include_router(portfolio.router)
app.include_router(simulate.router)
app.include_router(investment_simulator.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "ml_enabled": settings.ml_enabled}
