import { useEffect, useState } from "react";
import { api } from "@/api/client";
import { PageTransition } from "@/components/ui/PageTransition";
import { AnimatedCard } from "@/components/ui/AnimatedCard";

export function PortfolioPage() {
  const [holdings, setHoldings] = useState<
    {
      id: number;
      ticker: string;
      shares: number;
      cost_basis: number | null;
      current_value: number | null;
      gain_loss_pct: number | null;
    }[]
  >([]);
  const [rebalance, setRebalance] = useState<{ ticker: string; drift_pct: number; action: string }[]>([]);
  const [taxHints, setTaxHints] = useState<{ ticker: string; suggestion: string }[]>([]);
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [form, setForm] = useState({ ticker: "VTI", shares: 10, cost_basis: 0 });
  const [watchTicker, setWatchTicker] = useState("");

  const load = () => {
    api.listPortfolio().then(setHoldings);
    api.rebalance().then(setRebalance).catch(() => []);
    api.taxHints().then(setTaxHints).catch(() => []);
    api.watchlist().then((r) => setWatchlist(r.items));
  };

  useEffect(() => {
    load();
  }, []);

  const addHolding = async () => {
    await api.addPortfolio({
      ticker: form.ticker,
      shares: form.shares,
      cost_basis: form.cost_basis || undefined,
    });
    load();
  };

  return (
    <PageTransition>
      <h1 className="text-3xl font-bold mb-8">Portfolio tracker</h1>

      <AnimatedCard className="mb-6">
        <h2 className="font-semibold mb-4">Add holding</h2>
        <div className="flex flex-wrap gap-3">
          <input
            className="px-3 py-2 rounded-lg border border-border bg-background font-mono w-24"
            value={form.ticker}
            onChange={(e) => setForm({ ...form, ticker: e.target.value.toUpperCase() })}
          />
          <input
            type="number"
            placeholder="Shares"
            className="px-3 py-2 rounded-lg border border-border bg-background w-24"
            value={form.shares}
            onChange={(e) => setForm({ ...form, shares: +e.target.value })}
          />
          <input
            type="number"
            placeholder="Cost basis"
            className="px-3 py-2 rounded-lg border border-border bg-background w-32"
            value={form.cost_basis}
            onChange={(e) => setForm({ ...form, cost_basis: +e.target.value })}
          />
          <button onClick={addHolding} className="px-4 py-2 rounded-lg bg-accent text-accent-foreground">
            Add
          </button>
        </div>
      </AnimatedCard>

      <div className="grid md:grid-cols-2 gap-4 mb-8">
        {holdings.map((h) => (
          <AnimatedCard key={h.id}>
            <div className="flex justify-between">
              <span className="font-mono font-bold">{h.ticker}</span>
              <button
                className="text-xs text-muted-foreground"
                onClick={() => api.deletePortfolio(h.id).then(load)}
              >
                Remove
              </button>
            </div>
            <p className="text-sm text-muted-foreground">{h.shares} shares</p>
            {h.current_value != null && <p className="text-lg font-semibold">${h.current_value.toFixed(2)}</p>}
            {h.gain_loss_pct != null && (
              <p className={h.gain_loss_pct >= 0 ? "text-positive" : "text-negative"}>
                {h.gain_loss_pct >= 0 ? "+" : ""}
                {h.gain_loss_pct}%
              </p>
            )}
          </AnimatedCard>
        ))}
      </div>

      {rebalance.length > 0 && (
        <AnimatedCard className="mb-6">
          <h2 className="font-semibold mb-3 text-negative">Rebalancing suggested</h2>
          <ul className="space-y-2 text-sm">
            {rebalance.map((r) => (
              <li key={r.ticker}>
                <strong>{r.ticker}</strong>: {r.action} (drift {r.drift_pct}%)
              </li>
            ))}
          </ul>
        </AnimatedCard>
      )}

      {taxHints.length > 0 && (
        <AnimatedCard className="mb-6">
          <h2 className="font-semibold mb-3">Tax-loss hints</h2>
          <ul className="space-y-2 text-sm text-muted-foreground">
            {taxHints.map((t) => (
              <li key={t.ticker}>
                {t.ticker}: {t.suggestion}
              </li>
            ))}
          </ul>
        </AnimatedCard>
      )}

      <AnimatedCard>
        <h2 className="font-semibold mb-4">Watchlist</h2>
        <div className="flex gap-2 mb-3">
          <input
            className="px-3 py-2 rounded-lg border border-border bg-background font-mono"
            value={watchTicker}
            onChange={(e) => setWatchTicker(e.target.value.toUpperCase())}
            placeholder="Ticker"
          />
          <button
            onClick={() => api.addWatchlist(watchTicker).then(load)}
            className="px-4 py-2 rounded-lg bg-muted"
          >
            Add
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {watchlist.map((t) => (
            <span key={t} className="px-3 py-1 rounded-full bg-muted font-mono text-sm flex items-center gap-2">
              {t}
              <button onClick={() => api.removeWatchlist(t).then(load)} className="text-muted-foreground hover:text-negative">
                ×
              </button>
            </span>
          ))}
        </div>
      </AnimatedCard>
    </PageTransition>
  );
}
