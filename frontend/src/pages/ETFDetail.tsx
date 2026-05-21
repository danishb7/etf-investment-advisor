import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { api } from "@/api/client";
import { PageTransition } from "@/components/ui/PageTransition";
import { AnimatedCard } from "@/components/ui/AnimatedCard";
import { Skeleton } from "@/components/ui/Skeleton";
import { PriceChart } from "@/components/PriceChart";

const PERIODS = ["1m", "3m", "6m", "1y", "3y", "5y", "max"] as const;

export function ETFDetail() {
  const { ticker } = useParams<{ ticker: string }>();
  const [period, setPeriod] = useState<string>("1y");
  const [history, setHistory] = useState<{ date: string; close: number }[]>([]);
  const [stats, setStats] = useState<Record<string, number>>({});
  const [quote, setQuote] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async (p: string, refresh = false) => {
    if (!ticker) return;
    setLoading(true);
    try {
      const [hist, q] = await Promise.all([
        api.getHistory(ticker, p),
        api.getQuote(ticker, refresh),
      ]);
      setHistory(hist.data.map((d) => ({ date: d.date, close: d.close })));
      setStats(hist.stats);
      setQuote(q.price);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(period);
  }, [ticker, period]);

  useEffect(() => {
    if (!ticker) return;
    api.searchEtfs(ticker).then((r) => {
      const match =
        r.curated.find((e) => e.ticker === ticker.toUpperCase()) ||
        (r.lookup?.ticker === ticker.toUpperCase() ? r.lookup : null);
      if (match?.name) setName(match.name);
    }).catch(() => {});
  }, [ticker]);

  return (
    <PageTransition>
      <Link to="/etfs" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-accent mb-6">
        <ArrowLeft size={16} /> Back to ETFs
      </Link>

      <div className="flex flex-wrap justify-between items-start gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold font-mono">{ticker}</h1>
          {name && <p className="text-muted-foreground text-sm mt-1 max-w-xl">{name}</p>}
          {quote != null && (
            <p className="text-2xl font-semibold text-accent mt-1">${quote.toFixed(2)}</p>
          )}
        </div>
        <div className="flex flex-wrap gap-1">
          {PERIODS.map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                period === p ? "bg-accent text-accent-foreground" : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              {p.toUpperCase()}
            </button>
          ))}
          <button
            onClick={() => load(period, true)}
            className="px-3 py-1 rounded-lg text-sm bg-muted hover:bg-muted/80"
          >
            Refresh price
          </button>
        </div>
      </div>

      <AnimatedCard className="mb-6">
        {loading ? <Skeleton className="h-72" /> : <PriceChart data={history} />}
      </AnimatedCard>

      {!loading && Object.keys(stats).length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Return", value: `${stats.return_pct?.toFixed(1)}%` },
            { label: "Volatility", value: `${stats.volatility?.toFixed(1)}%` },
            { label: "Sharpe", value: stats.sharpe_ratio?.toFixed(2) },
            { label: "Max drawdown", value: `${stats.max_drawdown?.toFixed(1)}%` },
          ].map((s) => (
            <AnimatedCard key={s.label} className="p-4 text-center">
              <p className="text-xs text-muted-foreground">{s.label}</p>
              <p className="text-xl font-semibold mt-1">{s.value}</p>
            </AnimatedCard>
          ))}
        </div>
      )}
    </PageTransition>
  );
}
