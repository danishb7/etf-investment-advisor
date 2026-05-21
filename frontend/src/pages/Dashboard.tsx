import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { RefreshCw } from "lucide-react";
import { api, type RecommendResponse } from "@/api/client";
import { PageTransition } from "@/components/ui/PageTransition";
import { AnimatedCard } from "@/components/ui/AnimatedCard";
import { Skeleton } from "@/components/ui/Skeleton";
import { AllocationChart } from "@/components/AllocationChart";
import { ScoreCard } from "@/components/ScoreCard";

export function Dashboard() {
  const [data, setData] = useState<RecommendResponse | null>(null);
  const [macro, setMacro] = useState<Record<string, unknown> | null>(null);
  const [sentiment, setSentiment] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [rec, m, s] = await Promise.all([
        api.recommend(),
        api.getMacro(true).catch(() => null),
        api.getSentiment().catch(() => null),
      ]);
      setData(rec);
      setMacro(m);
      setSentiment(s);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const pieData =
    data?.recommendations.map((r) => ({
      name: r.ticker,
      value: r.allocation_pct,
    })) ?? [];

  return (
    <PageTransition>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Your portfolio</h1>
          <p className="text-muted-foreground mt-1">Personalized ETF recommendations</p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent text-accent-foreground text-sm font-medium hover:opacity-90 disabled:opacity-50"
        >
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-negative/10 text-negative text-sm">
          {error}
          {error.includes("onboarding") && (
            <Link to="/onboarding" className="block mt-2 underline">
              Complete onboarding
            </Link>
          )}
        </div>
      )}

      {loading && (
        <div className="grid md:grid-cols-2 gap-6">
          <Skeleton className="h-72" />
          <Skeleton className="h-72" />
        </div>
      )}

      {!loading && data && (
        <>
          {data.portfolio_warnings.length > 0 && (
            <AnimatedCard className="mb-6 border-negative/30">
              <p className="text-sm font-medium text-negative mb-2">Risk notes</p>
              <ul className="text-sm space-y-1 list-disc list-inside text-muted-foreground">
                {data.portfolio_warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </AnimatedCard>
          )}

          <div className="grid md:grid-cols-2 gap-6 mb-8">
            <AnimatedCard>
              <h2 className="font-semibold mb-4">Allocation</h2>
              <AllocationChart data={pieData} />
              <div className="flex gap-4 mt-4 text-sm text-muted-foreground">
                {data.weighted_expense_ratio != null && (
                  <span>Weighted ER: {(data.weighted_expense_ratio * 100).toFixed(2)}%</span>
                )}
                {data.estimated_volatility != null && (
                  <span>Est. vol: ~{data.estimated_volatility}%</span>
                )}
              </div>
            </AnimatedCard>

            <AnimatedCard delay={0.05}>
              <h2 className="font-semibold mb-4">Macro & sentiment</h2>
              {macro && (macro as { regime?: Record<string, string> }).regime && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {Object.entries((macro as { regime: Record<string, string> }).regime).map(([k, v]) => (
                    <span key={k} className="px-2 py-1 rounded-full bg-muted text-xs capitalize">
                      {k}: {v}
                    </span>
                  ))}
                </div>
              )}
              {(sentiment as { themes?: Record<string, { label: string; score: number }> })?.themes && (
                <div className="space-y-2">
                  {Object.entries(
                    (sentiment as { themes: Record<string, { label: string; score: number }> }).themes
                  ).map(([theme, t]) => (
                    <div key={theme} className="flex justify-between text-sm">
                      <span className="capitalize text-muted-foreground">{theme}</span>
                      <span className={t.score > 0.1 ? "text-positive" : t.score < -0.1 ? "text-negative" : ""}>
                        {t.label}
                      </span>
                    </div>
                  ))}
                </div>
              )}
              {!macro && !sentiment && (
                <p className="text-sm text-muted-foreground">Macro/sentiment data loading on next refresh.</p>
              )}
            </AnimatedCard>
          </div>

          <h2 className="text-xl font-semibold mb-4">Top picks</h2>
          <div className="grid gap-4">
            {data.recommendations.map((etf, i) => (
              <ScoreCard key={etf.ticker} etf={etf} index={i} />
            ))}
          </div>

          {data.near_misses.length > 0 && (
            <>
              <h2 className="text-xl font-semibold mt-10 mb-4">Near misses</h2>
              <div className="grid md:grid-cols-3 gap-4">
                {data.near_misses.map((etf, i) => (
                  <ScoreCard key={etf.ticker} etf={etf} index={i} />
                ))}
              </div>
            </>
          )}
        </>
      )}
    </PageTransition>
  );
}
