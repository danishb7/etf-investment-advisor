import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { api } from "@/api/client";
import { PageTransition } from "@/components/ui/PageTransition";
import { AnimatedCard } from "@/components/ui/AnimatedCard";
import { Skeleton } from "@/components/ui/Skeleton";
import { InlineError } from "@/components/ui/InlineError";
import { AllocationChart } from "@/components/AllocationChart";
import { ScoreCard } from "@/components/ScoreCard";

function formatCacheLabel(cached?: boolean, generatedAt?: string | null): string {
  if (!generatedAt) return "";
  const at = new Date(generatedAt);
  const mins = Math.floor((Date.now() - at.getTime()) / 60000);
  const age =
    mins < 1 ? "just now" : mins < 60 ? `${mins} min ago` : `${Math.floor(mins / 60)} hr ago`;
  if (cached) return `Updated ${age} · Cached`;
  return "Just updated";
}

export function Dashboard() {
  const queryClient = useQueryClient();
  const [macro, setMacro] = useState<Record<string, unknown> | null>(null);
  const [sentiment, setSentiment] = useState<Record<string, unknown> | null>(null);

  const {
    data,
    isLoading,
    error,
    isFetching,
  } = useQuery({
    queryKey: ["recommend"],
    queryFn: async () => {
      const [rec, m, s] = await Promise.all([
        api.getRecommend(),
        api.getMacro(true).catch(() => null),
        api.getSentiment().catch(() => null),
      ]);
      setMacro(m);
      setSentiment(s);
      return rec;
    },
  });

  const refreshMutation = useMutation({
    mutationFn: async () => {
      const rec = await api.refreshRecommend();
      const [m, s] = await Promise.all([
        api.getMacro(true).catch(() => null),
        api.getSentiment().catch(() => null),
      ]);
      setMacro(m);
      setSentiment(s);
      return rec;
    },
    onSuccess: (rec) => {
      queryClient.setQueryData(["recommend"], rec);
    },
  });

  const loading = isLoading || refreshMutation.isPending;
  const errorMessage =
    (error as Error | null)?.message || (refreshMutation.error as Error | null)?.message || "";

  const pieData =
    data?.recommendations.map((r) => ({
      name: r.ticker,
      value: r.allocation_pct,
    })) ?? [];

  const cacheLabel = formatCacheLabel(data?.cached, data?.generated_at);

  return (
    <PageTransition>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Your portfolio</h1>
          <p className="text-muted-foreground mt-1">Personalized ETF recommendations</p>
          {cacheLabel && !loading && (
            <p className="text-xs text-muted-foreground mt-1">{cacheLabel}</p>
          )}
        </div>
        <button
          onClick={() => refreshMutation.mutate()}
          disabled={loading || isFetching}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent text-accent-foreground text-sm font-medium hover:opacity-90 disabled:opacity-50"
        >
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      <InlineError message={errorMessage} />
      {errorMessage.includes("onboarding") && (
        <Link to="/onboarding" className="block -mt-4 mb-6 text-sm underline text-negative">
          Complete onboarding
        </Link>
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
