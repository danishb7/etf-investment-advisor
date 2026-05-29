import { describe, expect, it } from "vitest";
import {
  aggregateInvestedByTicker,
  formatFundingSummary,
  legsSummary,
} from "./investmentScenarioUtils";
import type { InvestmentScenario } from "@/api/client";

const baseScenario: InvestmentScenario = {
  id: 1,
  name: "Test",
  start_date: "2020-01-01",
  end_date: "2021-01-01",
  lump_sum: 5000,
  monthly_amount: 200,
  contribution_day: 15,
  legs: [
    { ticker: "VTI", allocation_pct: 60 },
    { ticker: "BND", allocation_pct: 40 },
  ],
  result: {
    start_date: "2020-01-01",
    end_date: "2021-01-01",
    total_invested: 1000,
    final_value: 1100,
    return_pct: 10,
    max_drawdown: -5,
    series: [],
    contributions: [
      {
        date: "2020-01-02",
        amount: 1000,
        buys: [
          { ticker: "VTI", amount: 600, price: 100, shares: 6 },
          { ticker: "BND", amount: 400, price: 50, shares: 8 },
        ],
      },
    ],
    holdings: [],
  },
  total_invested: 1000,
  final_value: 1100,
  return_pct: 10,
};

describe("aggregateInvestedByTicker", () => {
  it("sums buy amounts per ticker", () => {
    const map = aggregateInvestedByTicker(baseScenario.result!.contributions);
    expect(map.get("VTI")).toBe(600);
    expect(map.get("BND")).toBe(400);
  });
});

describe("formatFundingSummary", () => {
  it("includes lump and monthly", () => {
    const s = formatFundingSummary(baseScenario);
    expect(s).toContain("5,000");
    expect(s).toContain("200");
    expect(s).toContain("day 15");
  });
});

describe("legsSummary", () => {
  it("formats leg tickers and percentages", () => {
    expect(legsSummary(baseScenario.legs)).toBe("VTI 60% · BND 40%");
  });
});
