from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    lump_sum: float = 0
    monthly_sip: float = 0
    horizon_months: int = 60
    risk_tolerance: str = "balanced"
    goal: str = "wealth_building"
    tax_bracket: str | None = None
    max_expense_ratio: float = 0.5
    exclude_sectors: str = ""
    esg_preference: bool = False
    onboarding_complete: bool = True


class ProfileResponse(ProfileUpdate):
    id: int
    updated_at: datetime | None = None


class ScoreBreakdown(BaseModel):
    momentum: float
    sharpe: float
    volatility: float
    expense: float
    dividend: float = 0
    macro_fit: float = 0
    sentiment: float = 0
    ml: float | None = None


class ETFRecommendation(BaseModel):
    ticker: str
    name: str
    category: str
    sector: str
    final_score: float
    rule_score: float
    allocation_pct: float
    breakdown: ScoreBreakdown
    expense_ratio: float | None
    return_1y: float | None
    max_drawdown: float | None
    sharpe_ratio: float | None
    explanation: str
    risk_warning: str | None = None


class RecommendResponse(BaseModel):
    recommendations: list[ETFRecommendation]
    near_misses: list[ETFRecommendation]
    portfolio_warnings: list[str]
    weighted_expense_ratio: float | None
    estimated_volatility: float | None
    sector_exposure: dict[str, float]
    run_id: int | None = None


class HistoricalSimRequest(BaseModel):
    ticker: str
    amount: float
    start_date: str


class HistoricalSimPoint(BaseModel):
    date: str
    value: float


class HistoricalSimResponse(BaseModel):
    ticker: str
    initial_amount: float
    final_value: float
    return_pct: float
    max_drawdown: float
    series: list[HistoricalSimPoint]


class PaperPositionCreate(BaseModel):
    ticker: str
    amount_invested: float
    purchase_date: str | None = None


class PaperPositionResponse(BaseModel):
    id: int
    ticker: str
    amount_invested: float
    shares: float
    purchase_date: str
    current_price: float | None
    current_value: float | None
    gain_loss: float | None
    gain_loss_pct: float | None
    sparkline: list[float] = []


class PortfolioHoldingCreate(BaseModel):
    ticker: str
    shares: float
    cost_basis: float | None = None
    purchase_date: str | None = None


class PortfolioHoldingResponse(PortfolioHoldingCreate):
    id: int
    current_price: float | None = None
    current_value: float | None = None
    gain_loss: float | None = None
    gain_loss_pct: float | None = None


class RebalanceAlert(BaseModel):
    ticker: str
    current_pct: float
    target_pct: float
    drift_pct: float
    action: str


class ForwardSimRequest(BaseModel):
    monthly_amount: float | None = None
    lump_sum: float | None = None
    horizon_months: int = 60
    tickers: list[str] = Field(default_factory=list)
    simulations: int = 500


class ForwardSimResponse(BaseModel):
    median_final_value: float
    percentile_10: float
    percentile_90: float
    series: list[dict[str, Any]]


class WatchlistItemSchema(BaseModel):
    ticker: str


class TaxLossHint(BaseModel):
    ticker: str
    unrealized_loss: float
    suggestion: str


class ScenarioLeg(BaseModel):
    ticker: str
    allocation_pct: float
    start_date: str | None = None
    end_date: str | None = None


class InvestmentScenarioCreate(BaseModel):
    name: str
    start_date: str
    end_date: str | None = None
    lump_sum: float = 0
    monthly_amount: float = 0
    contribution_day: int = Field(default=1, ge=1, le=28)
    legs: list[ScenarioLeg]


class InvestmentScenarioUpdate(BaseModel):
    name: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    lump_sum: float | None = None
    monthly_amount: float | None = None
    contribution_day: int | None = Field(default=None, ge=1, le=28)
    legs: list[ScenarioLeg] | None = None


class InvestmentScenarioResponse(BaseModel):
    id: int
    name: str
    start_date: str
    end_date: str | None
    lump_sum: float
    monthly_amount: float
    contribution_day: int
    legs: list[dict]
    result: dict | None
    total_invested: float | None
    final_value: float | None
    return_pct: float | None
    created_at: datetime | None
    updated_at: datetime | None
