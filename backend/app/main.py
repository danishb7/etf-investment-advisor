import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import etfs, investment_simulator, macro_sentiment, paper, portfolio, profile, recommend, simulate
from app.config import settings
from app.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("app.request")


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info("%s %s %.0fms", request.method, request.url.path, duration_ms)
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.0f}"
        return response


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
app.add_middleware(TimingMiddleware)

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
