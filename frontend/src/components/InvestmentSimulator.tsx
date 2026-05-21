import { useEffect, useState } from "react";
import { Plus, Trash2, Play, RefreshCw } from "lucide-react";
import { api, type InvestmentScenario } from "@/api/client";
import { AnimatedCard } from "./ui/AnimatedCard";
import { PriceChart } from "./PriceChart";
import { TickerSearch } from "./TickerSearch";

type LegForm = {
  ticker: string;
  allocation_pct: number;
  start_date: string;
  end_date: string;
};

const emptyLeg = (): LegForm => ({
  ticker: "VTI",
  allocation_pct: 100,
  start_date: "",
  end_date: "",
});

export function InvestmentSimulator() {
  const [scenarios, setScenarios] = useState<InvestmentScenario[]>([]);
  const [selected, setSelected] = useState<InvestmentScenario | null>(null);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: "My investment plan",
    start_date: "2020-01-01",
    end_date: "",
    lump_sum: 5000,
    monthly_amount: 200,
    contribution_day: 1,
    legs: [emptyLeg()] as LegForm[],
  });

  const load = () => api.listInvestmentScenarios().then(setScenarios);

  useEffect(() => {
    load();
  }, []);

  const allocSum = form.legs.reduce((s, l) => s + l.allocation_pct, 0);

  const addLeg = () => {
    const n = form.legs.length + 1;
    const pct = Math.floor(100 / n);
    const legs = form.legs.map((l) => ({ ...l, allocation_pct: pct }));
    legs.push({ ...emptyLeg(), allocation_pct: 100 - pct * form.legs.length });
    setForm({ ...form, legs });
  };

  const removeLeg = (i: number) => {
    setForm({ ...form, legs: form.legs.filter((_, idx) => idx !== i) });
  };

  const saveAndRun = async () => {
    if (Math.abs(allocSum - 100) > 0.5) {
      alert(`Allocations must sum to 100% (currently ${allocSum.toFixed(1)}%)`);
      return;
    }
    setLoading(true);
    try {
      const created = await api.createInvestmentScenario({
        name: form.name,
        start_date: form.start_date,
        end_date: form.end_date || undefined,
        lump_sum: form.lump_sum,
        monthly_amount: form.monthly_amount,
        contribution_day: form.contribution_day,
        legs: form.legs.map((l) => ({
          ticker: l.ticker,
          allocation_pct: l.allocation_pct,
          start_date: l.start_date || undefined,
          end_date: l.end_date || undefined,
        })),
      });
      setSelected(created);
      load();
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const rerun = async (id: number) => {
    setLoading(true);
    try {
      const updated = await api.runInvestmentScenario(id);
      setSelected(updated);
      load();
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const deleteScenario = async (id: number) => {
    await api.deleteInvestmentScenario(id);
    if (selected?.id === id) setSelected(null);
    load();
  };

  const result = selected?.result;

  return (
    <div className="space-y-8">
      <AnimatedCard>
        <h2 className="text-xl font-semibold mb-1">Investment Simulator</h2>
        <p className="text-sm text-muted-foreground mb-6">
          Backtest a real plan: lump sum on start date + monthly installments on a fixed day, split across
          ETFs using actual historical prices. Per-ETF dates optional.
        </p>

        <div className="grid md:grid-cols-2 gap-4 mb-4">
          <label className="text-sm block">
            Plan name
            <input
              className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </label>
          <label className="text-sm block">
            Contribution day (1–28)
            <input
              type="number"
              min={1}
              max={28}
              className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
              value={form.contribution_day}
              onChange={(e) => setForm({ ...form, contribution_day: +e.target.value })}
            />
          </label>
          <label className="text-sm block">
            Start date
            <input
              type="date"
              className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
              value={form.start_date}
              onChange={(e) => setForm({ ...form, start_date: e.target.value })}
            />
          </label>
          <label className="text-sm block">
            End date (optional, default today)
            <input
              type="date"
              className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
              value={form.end_date}
              onChange={(e) => setForm({ ...form, end_date: e.target.value })}
            />
          </label>
          <label className="text-sm block">
            Lump sum on start date ($)
            <input
              type="number"
              className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
              value={form.lump_sum}
              onChange={(e) => setForm({ ...form, lump_sum: +e.target.value })}
            />
          </label>
          <label className="text-sm block">
            Monthly installment ($)
            <input
              type="number"
              className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
              value={form.monthly_amount}
              onChange={(e) => setForm({ ...form, monthly_amount: +e.target.value })}
            />
          </label>
        </div>

        <h3 className="font-medium mb-3">ETF allocation ({allocSum.toFixed(0)}% / 100%)</h3>
        <div className="space-y-3 mb-4">
          {form.legs.map((leg, i) => (
            <div key={i} className="flex flex-wrap gap-2 items-end p-3 rounded-lg bg-muted/40">
              <div className="w-28">
                <span className="text-xs text-muted-foreground">Ticker</span>
                <input
                  className="w-full px-2 py-1.5 rounded border border-border bg-background font-mono text-sm"
                  value={leg.ticker}
                  onChange={(e) => {
                    const legs = [...form.legs];
                    legs[i] = { ...leg, ticker: e.target.value.toUpperCase() };
                    setForm({ ...form, legs });
                  }}
                />
              </div>
              <div className="w-20">
                <span className="text-xs text-muted-foreground">%</span>
                <input
                  type="number"
                  className="w-full px-2 py-1.5 rounded border border-border bg-background text-sm"
                  value={leg.allocation_pct}
                  onChange={(e) => {
                    const legs = [...form.legs];
                    legs[i] = { ...leg, allocation_pct: +e.target.value };
                    setForm({ ...form, legs });
                  }}
                />
              </div>
              <div className="w-36">
                <span className="text-xs text-muted-foreground">From (opt.)</span>
                <input
                  type="date"
                  className="w-full px-2 py-1.5 rounded border border-border bg-background text-sm"
                  value={leg.start_date}
                  onChange={(e) => {
                    const legs = [...form.legs];
                    legs[i] = { ...leg, start_date: e.target.value };
                    setForm({ ...form, legs });
                  }}
                />
              </div>
              <div className="w-36">
                <span className="text-xs text-muted-foreground">Until (opt.)</span>
                <input
                  type="date"
                  className="w-full px-2 py-1.5 rounded border border-border bg-background text-sm"
                  value={leg.end_date}
                  onChange={(e) => {
                    const legs = [...form.legs];
                    legs[i] = { ...leg, end_date: e.target.value };
                    setForm({ ...form, legs });
                  }}
                />
              </div>
              <button
                type="button"
                onClick={() => removeLeg(i)}
                className="p-2 text-muted-foreground hover:text-negative"
                disabled={form.legs.length <= 1}
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
        <div className="flex flex-wrap gap-2 mb-2">
          <button type="button" onClick={addLeg} className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-muted text-sm">
            <Plus size={14} /> Add ETF
          </button>
        </div>
        <div className="mb-4 max-w-md">
          <TickerSearch />
        </div>
        <button
          onClick={saveAndRun}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-2 rounded-lg bg-accent text-accent-foreground font-medium disabled:opacity-50"
        >
          <Play size={16} />
          {loading ? "Running…" : "Save & simulate"}
        </button>
      </AnimatedCard>

      {result && selected && (
        <AnimatedCard>
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="font-semibold text-lg">{selected.name}</h3>
              <p className="text-sm text-muted-foreground">
                {result.start_date} → {result.end_date}
              </p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => rerun(selected.id)} className="p-2 rounded-lg bg-muted" title="Re-run">
                <RefreshCw size={16} />
              </button>
              <button onClick={() => deleteScenario(selected.id)} className="p-2 rounded-lg bg-muted text-negative">
                <Trash2 size={16} />
              </button>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 text-center">
            <div>
              <p className="text-xs text-muted-foreground">Total invested</p>
              <p className="text-xl font-bold">${result.total_invested?.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Final value</p>
              <p className="text-xl font-bold">${result.final_value?.toLocaleString()}</p>
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
          <PriceChart
            data={(result.series as { date: string; value: number }[]).map((p) => ({
              date: p.date,
              close: p.value,
            }))}
          />
          {result.contributions && (result.contributions as unknown[]).length > 0 && (
            <div className="mt-6">
              <h4 className="text-sm font-medium mb-2">Contributions ({(result.contributions as unknown[]).length})</h4>
              <ul className="text-xs text-muted-foreground max-h-32 overflow-y-auto space-y-1">
                {(result.contributions as { date: string; amount: number }[]).map((c, i) => (
                  <li key={i}>
                    {c.date}: ${c.amount.toLocaleString()}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </AnimatedCard>
      )}

      {scenarios.length > 0 && (
        <AnimatedCard>
          <h3 className="font-semibold mb-4">Saved plans</h3>
          <ul className="space-y-2">
            {scenarios.map((s) => (
              <li key={s.id}>
                <button
                  type="button"
                  onClick={() => setSelected(s)}
                  className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                    selected?.id === s.id ? "border-accent bg-accent/5" : "border-border hover:bg-muted/50"
                  }`}
                >
                  <span className="font-medium">{s.name}</span>
                  <span className="block text-xs text-muted-foreground mt-0.5">
                    {s.start_date}
                    {s.end_date ? ` → ${s.end_date}` : " → today"} · ${s.total_invested?.toLocaleString() ?? "—"} invested
                    {s.return_pct != null && (
                      <span className={s.return_pct >= 0 ? " text-positive" : " text-negative"}>
                        {" "}
                        · {s.return_pct > 0 ? "+" : ""}
                        {s.return_pct}%
                      </span>
                    )}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </AnimatedCard>
      )}
    </div>
  );
}
