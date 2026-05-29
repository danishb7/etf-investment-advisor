const BASE = "/api";

type ValidationErrorItem = { msg?: string; loc?: unknown[]; type?: string };

export function formatApiError(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        const d = item as ValidationErrorItem;
        return d.msg ?? JSON.stringify(item);
      })
      .join("; ");
  }
  if (detail && typeof detail === "object" && "msg" in detail) {
    return String((detail as ValidationErrorItem).msg);
  }
  return fallback;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(formatApiError(err.detail, res.statusText));
  }
  return res.json();
}

export interface Profile {
  id: number;
  lump_sum: number;
  monthly_sip: number;
  horizon_months: number;
  risk_tolerance: string;
  goal: string;
  tax_bracket: string | null;
  max_expense_ratio: number;
  exclude_sectors: string;
  esg_preference: boolean;
  onboarding_complete: boolean;
  updated_at?: string;
}

export interface ScoreBreakdown {
  momentum: number;
  sharpe: number;
  volatility: number;
  expense: number;
  dividend: number;
  macro_fit: number;
  sentiment: number;
  esg_fit?: number;
  shariah_fit?: number;
  ml?: number;
}

export interface ETFRecommendation {
  ticker: string;
  name: string;
  category: string;
  sector: string;
  final_score: number;
  rule_score: number;
  allocation_pct: number;
  breakdown: ScoreBreakdown;
  expense_ratio: number | null;
  return_1y: number | null;
  max_drawdown: number | null;
  sharpe_ratio: number | null;
  explanation: string;
  risk_warning: string | null;
}

export interface RecommendResponse {
  recommendations: ETFRecommendation[];
  near_misses: ETFRecommendation[];
  portfolio_warnings: string[];
  weighted_expense_ratio: number | null;
  estimated_volatility: number | null;
  sector_exposure: Record<string, number>;
  run_id: number | null;
  cached?: boolean;
  generated_at?: string | null;
}

export const api = {
  getProfile: () => request<Profile>("/profile"),
  updateProfile: (data: Partial<Profile>) =>
    request<Profile>("/profile", { method: "PUT", body: JSON.stringify(data) }),

  getRecommend: (force = false) =>
    request<RecommendResponse>(`/recommend?force=${force}`),
  refreshRecommend: () => request<RecommendResponse>("/recommend", { method: "POST" }),
  recommendHistory: () => request<{ runs: { id: number; created_at: string; preview: unknown[] }[] }>("/recommend/history"),

  listEtfs: () => request<{ etfs: { ticker: string; name: string; category: string; sector: string }[] }>("/etfs"),
  searchEtfs: (q: string) =>
    request<{
      query: string;
      curated: { ticker: string; name: string; category: string; sector: string; in_universe: boolean }[];
      lookup: {
        ticker: string;
        name: string;
        category: string;
        sector: string;
        in_universe: boolean;
        has_data?: boolean;
      } | null;
    }>(`/etfs/search?q=${encodeURIComponent(q)}`),
  prefetch: () => request<{ prefetched: number }>("/etfs/prefetch", { method: "POST" }),
  getHistory: (ticker: string, period: string) =>
    request<{ ticker: string; period: string; data: { date: string; close: number }[]; stats: Record<string, number> }>(
      `/etfs/${ticker}/history?period=${period}`
    ),
  getQuote: (ticker: string, refresh = false) =>
    request<{ ticker: string; price: number; as_of: string }>(`/etfs/${ticker}/quote?refresh=${refresh}`),

  getMacro: (force = false) => request<Record<string, unknown>>(`/macro?force=${force}`),
  getSentiment: (force = false) => request<Record<string, unknown>>(`/sentiment?force=${force}`),

  historicalSim: (data: { ticker: string; amount: number; start_date: string }) =>
    request<{
      ticker: string;
      initial_amount: number;
      final_value: number;
      return_pct: number;
      max_drawdown: number;
      series: { date: string; value: number }[];
    }>("/simulate/historical", { method: "POST", body: JSON.stringify(data) }),

  forwardSim: (data: {
    monthly_amount?: number;
    lump_sum?: number;
    horizon_months: number;
    tickers: string[];
    simulations?: number;
  }) =>
    request<{
      median_final_value: number;
      percentile_10: number;
      percentile_90: number;
      series: { month: number; value: number }[];
    }>("/simulate/forward", { method: "POST", body: JSON.stringify(data) }),

  listPaper: () =>
    request<
      {
        id: number;
        ticker: string;
        amount_invested: number;
        shares: number;
        purchase_date: string;
        current_price: number | null;
        current_value: number | null;
        gain_loss: number | null;
        gain_loss_pct: number | null;
        sparkline: number[];
      }[]
    >("/paper-positions"),

  createPaper: (data: { ticker: string; amount_invested: number; purchase_date?: string }) =>
    request("/paper-positions", { method: "POST", body: JSON.stringify(data) }),

  deletePaper: (id: number) => request(`/paper-positions/${id}`, { method: "DELETE" }),

  listPortfolio: () =>
    request<
      {
        id: number;
        ticker: string;
        shares: number;
        cost_basis: number | null;
        current_value: number | null;
        gain_loss: number | null;
        gain_loss_pct: number | null;
      }[]
    >("/portfolio"),

  addPortfolio: (data: { ticker: string; shares: number; cost_basis?: number }) =>
    request("/portfolio", { method: "POST", body: JSON.stringify(data) }),

  deletePortfolio: (id: number) => request(`/portfolio/${id}`, { method: "DELETE" }),

  rebalance: () =>
    request<{ ticker: string; current_pct: number; target_pct: number; drift_pct: number; action: string }[]>(
      "/portfolio/rebalance"
    ),

  taxHints: () => request<{ ticker: string; unrealized_loss: number; suggestion: string }[]>("/portfolio/tax-hints"),

  watchlist: () => request<{ items: string[] }>("/watchlist"),
  addWatchlist: (ticker: string) =>
    request("/watchlist", { method: "POST", body: JSON.stringify({ ticker }) }),
  removeWatchlist: (ticker: string) => request(`/watchlist/${ticker}`, { method: "DELETE" }),

  listInvestmentScenarios: () => request<InvestmentScenario[]>("/investment-simulator"),
  getInvestmentScenario: (id: number) => request<InvestmentScenario>(`/investment-simulator/${id}`),
  createInvestmentScenario: (data: InvestmentScenarioInput) =>
    request<InvestmentScenario>("/investment-simulator", { method: "POST", body: JSON.stringify(data) }),
  updateInvestmentScenario: (id: number, data: Partial<InvestmentScenarioInput>) =>
    request<InvestmentScenario>(`/investment-simulator/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  runInvestmentScenario: (id: number) =>
    request<InvestmentScenario>(`/investment-simulator/${id}/run`, { method: "POST" }),
  deleteInvestmentScenario: (id: number) =>
    request(`/investment-simulator/${id}`, { method: "DELETE" }),
};

export interface ScenarioLegInput {
  ticker: string;
  allocation_pct: number;
  start_date?: string;
  end_date?: string;
}

export interface InvestmentScenarioInput {
  name: string;
  start_date: string;
  end_date?: string;
  lump_sum: number;
  monthly_amount: number;
  contribution_day: number;
  legs: ScenarioLegInput[];
}

export interface InvestmentScenario {
  id: number;
  name: string;
  start_date: string;
  end_date: string | null;
  lump_sum: number;
  monthly_amount: number;
  contribution_day: number;
  legs: ScenarioLegInput[];
  result: {
    start_date: string;
    end_date: string;
    total_invested: number;
    final_value: number;
    return_pct: number;
    max_drawdown: number;
    series: { date: string; value: number; invested: number }[];
    contributions: { date: string; amount: number; buys: unknown[] }[];
    holdings: { ticker: string; shares: number; value: number }[];
  } | null;
  total_invested: number | null;
  final_value: number | null;
  return_pct: number | null;
  created_at?: string;
  updated_at?: string;
}
