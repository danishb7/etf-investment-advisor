import type { InvestmentScenario, ScenarioLegInput } from "@/api/client";

export interface ContributionBuy {
  ticker: string;
  amount: number;
  price: number;
  shares: number;
}

export interface Contribution {
  date: string;
  amount: number;
  buys: ContributionBuy[];
}

export interface HoldingRow {
  ticker: string;
  shares: number;
  value: number;
  last_price?: number;
}

export function aggregateInvestedByTicker(contributions: Contribution[]): Map<string, number> {
  const map = new Map<string, number>();
  for (const c of contributions) {
    for (const b of c.buys ?? []) {
      map.set(b.ticker, (map.get(b.ticker) ?? 0) + b.amount);
    }
  }
  return map;
}

export function formatFundingSummary(scenario: InvestmentScenario): string {
  const parts: string[] = [];
  if (scenario.lump_sum > 0) {
    parts.push(`$${scenario.lump_sum.toLocaleString()} lump on ${scenario.start_date}`);
  }
  if (scenario.monthly_amount > 0) {
    parts.push(`$${scenario.monthly_amount.toLocaleString()}/mo (day ${scenario.contribution_day})`);
  }
  return parts.join(" · ") || "No lump sum or monthly amount";
}

export function formatDateRange(scenario: InvestmentScenario): string {
  const end = scenario.end_date ?? "today";
  return `${scenario.start_date} → ${end}`;
}

export function legsSummary(legs: ScenarioLegInput[]): string {
  return legs.map((l) => `${l.ticker} ${l.allocation_pct}%`).join(" · ");
}

export function parseContributions(
  raw: InvestmentScenario["result"]
): Contribution[] {
  if (!raw?.contributions) return [];
  return raw.contributions as Contribution[];
}

export function parseHoldings(raw: InvestmentScenario["result"]): HoldingRow[] {
  if (!raw?.holdings) return [];
  return raw.holdings as HoldingRow[];
}
