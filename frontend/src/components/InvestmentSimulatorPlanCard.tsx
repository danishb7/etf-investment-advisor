import { ChevronRight } from "lucide-react";
import type { InvestmentScenario } from "@/api/client";
import {
  aggregateInvestedByTicker,
  formatDateRange,
  formatFundingSummary,
  legsSummary,
  parseContributions,
} from "@/lib/investmentScenarioUtils";

interface Props {
  scenario: InvestmentScenario;
  selected: boolean;
  onSelect: () => void;
}

export function InvestmentSimulatorPlanCard({ scenario, selected, onSelect }: Props) {
  const contributions = parseContributions(scenario.result);
  const investedByTicker = aggregateInvestedByTicker(contributions);
  const investedEntries = [...investedByTicker.entries()].sort((a, b) => b[1] - a[1]);

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      aria-label={
        selected
          ? `${scenario.name}, currently showing details`
          : `View details for ${scenario.name}`
      }
      className={`group w-full text-left px-4 py-3 rounded-lg border transition-colors ${
        selected ? "border-accent bg-accent/5 ring-1 ring-accent/30" : "border-border hover:bg-muted/50"
      }`}
    >
      <div className="flex justify-between items-start gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-medium truncate">{scenario.name}</span>
          {selected && (
            <span className="shrink-0 text-[10px] uppercase tracking-wide font-medium text-accent px-1.5 py-0.5 rounded bg-accent/10">
              Active
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {scenario.return_pct != null && (
            <span
              className={`text-sm font-semibold ${
                scenario.return_pct >= 0 ? "text-positive" : "text-negative"
              }`}
            >
              {scenario.return_pct > 0 ? "+" : ""}
              {scenario.return_pct}%
            </span>
          )}
          <ChevronRight
            size={18}
            className={`text-muted-foreground transition-transform duration-200 ${
              selected ? "rotate-90 text-accent" : "group-hover:translate-x-0.5"
            }`}
            aria-hidden
          />
        </div>
      </div>

      <p className="text-xs text-muted-foreground mt-1">{formatDateRange(scenario)}</p>
      <p className="text-xs text-muted-foreground mt-0.5">{formatFundingSummary(scenario)}</p>

      <div className="flex flex-wrap gap-1.5 mt-2">
        {scenario.legs.map((leg) => (
          <span
            key={leg.ticker}
            className="px-2 py-0.5 rounded-full bg-muted text-xs font-mono"
            title="Target allocation"
          >
            {leg.ticker} {leg.allocation_pct}%
          </span>
        ))}
      </div>

      {investedEntries.length > 0 ? (
        <p className="text-xs mt-2 text-muted-foreground">
          <span className="text-foreground/80">Invested: </span>
          {investedEntries
            .map(([t, amt]) => `${t} $${amt.toLocaleString(undefined, { maximumFractionDigits: 0 })}`)
            .join(" · ")}
        </p>
      ) : (
        <p className="text-xs mt-2 text-muted-foreground">
          <span className="text-foreground/80">Allocation: </span>
          {legsSummary(scenario.legs)}
        </p>
      )}

      {scenario.total_invested != null && (
        <p className="text-xs mt-1 text-muted-foreground">
          ${scenario.total_invested.toLocaleString()} total
          {scenario.final_value != null && ` → $${scenario.final_value.toLocaleString()} final`}
        </p>
      )}
    </button>
  );
}
