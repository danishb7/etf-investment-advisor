import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api } from "@/api/client";
import { InlineError } from "@/components/ui/InlineError";
import { PageTransition } from "@/components/ui/PageTransition";
import { AnimatedCard } from "@/components/ui/AnimatedCard";
import { PriceChart } from "@/components/PriceChart";
import { InvestmentSimulator } from "@/components/InvestmentSimulator";

export function Simulate() {
  const [tab, setTab] = useState<"investment" | "historical" | "paper" | "forward">("investment");
  const [ticker, setTicker] = useState("VTI");
  const [amount, setAmount] = useState(100);
  const [startDate, setStartDate] = useState("2020-01-01");
  const [histResult, setHistResult] = useState<{
    final_value: number;
    return_pct: number;
    max_drawdown: number;
    series: { date: string; value: number }[];
  } | null>(null);
  const [paper, setPaper] = useState<
    {
      id: number;
      ticker: string;
      amount_invested: number;
      current_value: number | null;
      gain_loss: number | null;
      gain_loss_pct: number | null;
      sparkline: number[];
    }[]
  >([]);
  const [paperTicker, setPaperTicker] = useState("SPY");
  const [paperAmount, setPaperAmount] = useState(100);
  const [forwardResult, setForwardResult] = useState<{
    median_final_value: number;
    percentile_10: number;
    percentile_90: number;
    series: { month: number; value: number }[];
  } | null>(null);
  const [profile, setProfile] = useState<{ monthly_sip: number; lump_sum: number; horizon_months: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadPaper = () => api.listPaper().then(setPaper);

  useEffect(() => {
    loadPaper();
    api.getProfile().then(setProfile).catch(() => {});
  }, []);

  const runHistorical = async () => {
    setLoading(true);
    setError("");
    try {
      const r = await api.historicalSim({ ticker, amount, start_date: startDate });
      setHistResult(r);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const addPaper = async () => {
    setError("");
    try {
      await api.createPaper({ ticker: paperTicker, amount_invested: paperAmount });
      loadPaper();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const runForward = async () => {
    if (!profile) return;
    setLoading(true);
    setError("");
    try {
      const r = await api.forwardSim({
        monthly_amount: profile.monthly_sip,
        lump_sum: profile.lump_sum,
        horizon_months: profile.horizon_months,
        tickers: [ticker],
      });
      setForwardResult(r);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: "investment" as const, label: "Investment Simulator" },
    { id: "historical" as const, label: "Historical what-if" },
    { id: "paper" as const, label: "Paper holdings" },
    { id: "forward" as const, label: "Forward projection (Monte Carlo)" },
  ];

  return (
    <PageTransition>
      <h1 className="text-3xl font-bold mb-2">Simulate</h1>
      <p className="text-muted-foreground mb-6">Explore how investments could have performed</p>

      <InlineError message={error} />

      <div className="flex gap-2 mb-8 flex-wrap">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-lg text-sm ${
              tab === t.id ? "bg-accent text-accent-foreground" : "bg-muted text-muted-foreground"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "investment" && <InvestmentSimulator />}

      {tab === "historical" && (
        <AnimatedCard>
          <div className="grid md:grid-cols-3 gap-4 mb-4">
            <label className="text-sm">
              Ticker
              <input
                className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background font-mono"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
              />
            </label>
            <label className="text-sm">
              Amount ($)
              <input
                type="number"
                className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
                value={amount}
                onChange={(e) => setAmount(+e.target.value)}
              />
            </label>
            <label className="text-sm">
              Start date
              <input
                type="date"
                className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </label>
          </div>
          <button
            onClick={runHistorical}
            disabled={loading}
            className="px-6 py-2 rounded-lg bg-accent text-accent-foreground font-medium disabled:opacity-50"
          >
            Run simulation
          </button>
          {histResult && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-6">
              <div className="grid grid-cols-3 gap-4 mb-4 text-center">
                <div>
                  <p className="text-xs text-muted-foreground">Final value</p>
                  <p className="text-xl font-bold">${histResult.final_value.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Return</p>
                  <p className={`text-xl font-bold ${histResult.return_pct >= 0 ? "text-positive" : "text-negative"}`}>
                    {histResult.return_pct > 0 ? "+" : ""}
                    {histResult.return_pct}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Max drawdown</p>
                  <p className="text-xl font-bold">{histResult.max_drawdown}%</p>
                </div>
              </div>
              <PriceChart data={histResult.series.map((s) => ({ date: s.date, close: s.value }))} />
            </motion.div>
          )}
        </AnimatedCard>
      )}

      {tab === "paper" && (
        <div className="space-y-6">
          <AnimatedCard>
            <h2 className="font-semibold mb-4">Track a virtual position</h2>
            <div className="flex flex-wrap gap-4 mb-4">
              <input
                className="px-3 py-2 rounded-lg border border-border bg-background font-mono w-24"
                value={paperTicker}
                onChange={(e) => setPaperTicker(e.target.value.toUpperCase())}
                placeholder="Ticker"
              />
              <input
                type="number"
                className="px-3 py-2 rounded-lg border border-border bg-background w-32"
                value={paperAmount}
                onChange={(e) => setPaperAmount(+e.target.value)}
              />
              <button onClick={addPaper} className="px-4 py-2 rounded-lg bg-accent text-accent-foreground">
                Add ${paperAmount}
              </button>
              <button onClick={loadPaper} className="px-4 py-2 rounded-lg bg-muted">
                Refresh prices
              </button>
            </div>
          </AnimatedCard>
          <div className="grid md:grid-cols-2 gap-4">
            {paper.map((p) => (
              <AnimatedCard key={p.id}>
                <div className="flex justify-between">
                  <span className="font-mono font-bold text-lg">{p.ticker}</span>
                  <button
                    className="text-xs text-muted-foreground hover:text-negative"
                    onClick={() => api.deletePaper(p.id).then(loadPaper)}
                  >
                    Remove
                  </button>
                </div>
                <p className="text-sm text-muted-foreground">Invested ${p.amount_invested}</p>
                {p.current_value != null && (
                  <motion.p
                    key={p.current_value}
                    initial={{ backgroundColor: "hsl(var(--accent) / 0.2)" }}
                    animate={{ backgroundColor: "transparent" }}
                    transition={{ duration: 0.5 }}
                    className="text-2xl font-bold mt-2 rounded px-1"
                  >
                    ${p.current_value.toFixed(2)}
                  </motion.p>
                )}
                {p.gain_loss_pct != null && (
                  <p className={`text-sm font-medium ${p.gain_loss_pct >= 0 ? "text-positive" : "text-negative"}`}>
                    {p.gain_loss_pct >= 0 ? "+" : ""}
                    {p.gain_loss_pct}% (${p.gain_loss?.toFixed(2)})
                  </p>
                )}
                {p.sparkline.length > 0 && (
                  <div className="h-12 mt-3">
                    <PriceChart
                      data={p.sparkline.map((v, i) => ({
                        date: String(i),
                        close: v,
                      }))}
                    />
                  </div>
                )}
              </AnimatedCard>
            ))}
          </div>
        </div>
      )}

      {tab === "forward" && (
        <AnimatedCard>
          <p className="text-sm text-muted-foreground mb-4">
            Monte Carlo projection using your profile SIP/lump sum over {profile?.horizon_months ?? "—"} months
          </p>
          <button
            onClick={runForward}
            disabled={loading || !profile}
            className="px-6 py-2 rounded-lg bg-accent text-accent-foreground font-medium disabled:opacity-50"
          >
            Run projection
          </button>
          {forwardResult && (
            <div className="mt-6">
              <div className="grid grid-cols-3 gap-4 mb-4 text-center text-sm">
                <div>
                  <p className="text-muted-foreground">Median</p>
                  <p className="font-bold text-lg">${forwardResult.median_final_value.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">10th %ile</p>
                  <p className="font-bold">${forwardResult.percentile_10.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">90th %ile</p>
                  <p className="font-bold">${forwardResult.percentile_90.toLocaleString()}</p>
                </div>
              </div>
              <PriceChart
                data={forwardResult.series.map((s) => ({
                  date: `M${s.month}`,
                  close: s.value,
                }))}
              />
            </div>
          )}
        </AnimatedCard>
      )}
    </PageTransition>
  );
}
