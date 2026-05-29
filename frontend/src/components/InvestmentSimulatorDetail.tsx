import { useState } from "react";
import { RefreshCw, Trash2, ChevronDown, ChevronRight } from "lucide-react";
import type { InvestmentScenario } from "@/api/client";
import { AnimatedCard } from "./ui/AnimatedCard";
import { PriceChart } from "./PriceChart";
import {
  aggregateInvestedByTicker,
  formatDateRange,
  formatFundingSummary,
  parseContributions,
  parseHoldings,
} from "@/lib/investmentScenarioUtils";

interface Props {
  scenario: InvestmentScenario;
  onRerun: (id: number) => void;
  onDelete: (id: number) => void;
  loading: boolean;
}

function money(n: number | undefined | null) {
  if (n == null) return "—";
  return `$${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

export function InvestmentSimulatorDetail({ scenario, onRerun, onDelete, loading }: Props) {
  const result = scenario.result;
  const contributions = parseContributions(result);
  const holdings = parseHoldings(result);
  const investedByTicker = aggregateInvestedByTicker(contributions);
  const [expandedContrib, setExpandedContrib] = useState<number | null>(null);

  if (!result) {
    return (
      <AnimatedCard>
        <div className="flex justify-between items-start">
          <div>
            <h3 className="font-semibold text-lg">{scenario.name}</h3>
            <p className="text-sm text-muted-foreground mt-1">No backtest results yet.</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => onRerun(scenario.id)}
              disabled={loading}
              className="p-2 rounded-lg bg-muted"
              title="Run backtest"
            >
              <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            </button>
            <button onClick={() => onDelete(scenario.id)} className="p-2 rounded-lg bg-muted text-negative">
              <Trash2 size={16} />
            </button>
          </div>
        </div>
        <p className="text-sm text-muted-foreground mt-4">{formatFundingSummary(scenario)}</p>
        <div className="flex flex-wrap gap-2 mt-3">
          {scenario.legs.map((leg) => (
            <span key={leg.ticker} className="px-2 py-1 rounded-full bg-muted text-xs font-mono">
              {leg.ticker} {leg.allocation_pct}%
            </span>
          ))}
        </div>
      </AnimatedCard>
    );
  }

  const investedRows = [...investedByTicker.entries()].sort((a, b) => b[1] - a[1]);

  return (
    <AnimatedCard>
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="font-semibold text-lg">{scenario.name}</h3>
          <p className="text-sm text-muted-foreground">{formatDateRange(scenario)}</p>
          <p className="text-sm text-muted-foreground mt-1">{formatFundingSummary(scenario)}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => onRerun(scenario.id)}
            disabled={loading}
            className="p-2 rounded-lg bg-muted"
            title="Re-run backtest"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          </button>
          <button onClick={() => onDelete(scenario.id)} className="p-2 rounded-lg bg-muted text-negative">
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8 text-center">
        <div>
          <p className="text-xs text-muted-foreground">Total invested</p>
          <p className="text-xl font-bold">{money(result.total_invested)}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Final value</p>
          <p className="text-xl font-bold">{money(result.final_value)}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Return</p>
          <p className={`text-xl font-bold ${(result.return_pct ?? 0) >= 0 ? "text-positive" : "text-negative"}`}>
            {(result.return_pct ?? 0) > 0 ? "+" : ""}
            {result.return_pct}%
          </p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Max drawdown</p>
          <p className="text-xl font-bold">{result.max_drawdown}%</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <div>
          <h4 className="text-sm font-semibold mb-3">Planned allocation</h4>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-muted-foreground border-b border-border">
                  <th className="px-3 py-2">ETF</th>
                  <th className="px-3 py-2">Target %</th>
                  <th className="px-3 py-2">Leg dates</th>
                </tr>
              </thead>
              <tbody>
                {scenario.legs.map((leg) => (
                  <tr key={leg.ticker} className="border-b border-border/50 last:border-0">
                    <td className="px-3 py-2 font-mono text-accent">{leg.ticker}</td>
                    <td className="px-3 py-2">{leg.allocation_pct}%</td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">
                      {leg.start_date || leg.end_date
                        ? `${leg.start_date || scenario.start_date} → ${leg.end_date || result.end_date}`
                        : "Full plan period"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <h4 className="text-sm font-semibold mb-3">Total invested by ETF (simulated)</h4>
          {investedRows.length === 0 ? (
            <p className="text-sm text-muted-foreground">No buy data available.</p>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-muted-foreground border-b border-border">
                    <th className="px-3 py-2">ETF</th>
                    <th className="px-3 py-2">Invested</th>
                    <th className="px-3 py-2">Share of total</th>
                  </tr>
                </thead>
                <tbody>
                  {investedRows.map(([ticker, amt]) => (
                    <tr key={ticker} className="border-b border-border/50 last:border-0">
                      <td className="px-3 py-2 font-mono text-accent">{ticker}</td>
                      <td className="px-3 py-2">{money(amt)}</td>
                      <td className="px-3 py-2 text-muted-foreground">
                        {result.total_invested > 0
                          ? `${((amt / result.total_invested) * 100).toFixed(1)}%`
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {holdings.length > 0 && (
        <div className="mb-8">
          <h4 className="text-sm font-semibold mb-3">End holdings</h4>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-muted-foreground border-b border-border">
                  <th className="px-3 py-2">ETF</th>
                  <th className="px-3 py-2">Shares</th>
                  <th className="px-3 py-2">Value</th>
                </tr>
              </thead>
              <tbody>
                {holdings.map((h) => (
                  <tr key={h.ticker} className="border-b border-border/50 last:border-0">
                    <td className="px-3 py-2 font-mono text-accent">{h.ticker}</td>
                    <td className="px-3 py-2">{h.shares.toLocaleString()}</td>
                    <td className="px-3 py-2">{money(h.value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <h4 className="text-sm font-semibold mb-3">Portfolio value over time</h4>
      <PriceChart
        data={result.series.map((p) => ({
          date: p.date,
          close: p.value,
        }))}
      />

      {contributions.length > 0 && (
        <div className="mt-8">
          <h4 className="text-sm font-semibold mb-3">
            Contributions ({contributions.length})
          </h4>
          <ul className="space-y-2 max-h-80 overflow-y-auto">
            {contributions.map((c, i) => {
              const open = expandedContrib === i;
              return (
                <li key={i} className="rounded-lg border border-border overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setExpandedContrib(open ? null : i)}
                    className="w-full flex items-center justify-between px-3 py-2 text-sm hover:bg-muted/50"
                  >
                    <span className="flex items-center gap-2">
                      {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      <span className="font-medium">{c.date}</span>
                    </span>
                    <span className="text-muted-foreground">{money(c.amount)} total</span>
                  </button>
                  {open && c.buys.length > 0 && (
                    <ul className="px-3 pb-3 pt-1 space-y-1 text-xs border-t border-border bg-muted/20">
                      {c.buys.map((b, j) => (
                        <li key={j} className="flex justify-between gap-4">
                          <span className="font-mono text-accent">{b.ticker}</span>
                          <span className="text-muted-foreground">
                            {money(b.amount)} @ ${b.price.toFixed(2)} · {b.shares.toLocaleString()} sh
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </AnimatedCard>
  );
}
