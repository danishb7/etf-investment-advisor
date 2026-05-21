from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InvestorProfile(Base):
    __tablename__ = "investor_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    lump_sum: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_sip: Mapped[float] = mapped_column(Float, default=0.0)
    horizon_months: Mapped[int] = mapped_column(Integer, default=60)
    risk_tolerance: Mapped[str] = mapped_column(String(32), default="balanced")
    goal: Mapped[str] = mapped_column(String(64), default="wealth_building")
    tax_bracket: Mapped[str | None] = mapped_column(String(32), nullable=True)
    max_expense_ratio: Mapped[float] = mapped_column(Float, default=0.5)
    exclude_sectors: Mapped[str] = mapped_column(Text, default="")
    esg_preference: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PriceCache(Base):
    __tablename__ = "price_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    period: Mapped[str] = mapped_column(String(8))
    data_json: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FundamentalCache(Base):
    __tablename__ = "fundamental_cache"

    ticker: Mapped[str] = mapped_column(String(16), primary_key=True)
    data_json: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MacroCache(Base):
    __tablename__ = "macro_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    data_json: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SentimentCache(Base):
    __tablename__ = "sentiment_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    data_json: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PaperPosition(Base):
    __tablename__ = "paper_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(16))
    amount_invested: Mapped[float] = mapped_column(Float)
    shares: Mapped[float] = mapped_column(Float)
    purchase_date: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(16))
    shares: Mapped[float] = mapped_column(Float)
    cost_basis: Mapped[float | None] = mapped_column(Float, nullable=True)
    purchase_date: Mapped[str | None] = mapped_column(String(16), nullable=True)


class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    result_json: Mapped[str] = mapped_column(Text)
    macro_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WatchlistItem(Base):
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(16), unique=True)


class LastRecommendation(Base):
    __tablename__ = "last_recommendation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    allocations_json: Mapped[str] = mapped_column(Text, default="{}")


class InvestmentScenario(Base):
    """Saved investment plan backtested on real historical prices."""

    __tablename__ = "investment_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    start_date: Mapped[str] = mapped_column(String(16))
    end_date: Mapped[str | None] = mapped_column(String(16), nullable=True)
    lump_sum: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_amount: Mapped[float] = mapped_column(Float, default=0.0)
    contribution_day: Mapped[int] = mapped_column(Integer, default=1)
    legs_json: Mapped[str] = mapped_column(Text)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_invested: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    return_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
