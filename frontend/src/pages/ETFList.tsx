import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/api/client";
import { PageTransition } from "@/components/ui/PageTransition";
import { AnimatedCard } from "@/components/ui/AnimatedCard";
import { Skeleton } from "@/components/ui/Skeleton";
import { TickerSearch } from "@/components/TickerSearch";

export function ETFList() {
  const [etfs, setEtfs] = useState<{ ticker: string; name: string; category: string; sector: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");

  useEffect(() => {
    api.listEtfs().then((r) => {
      setEtfs(r.etfs);
      setLoading(false);
    });
  }, []);

  const categories = useMemo(() => {
    const cats = new Set(etfs.map((e) => e.category));
    return ["all", ...Array.from(cats).sort()];
  }, [etfs]);

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase();
    return etfs.filter((e) => {
      const matchCat = categoryFilter === "all" || e.category === categoryFilter;
      const matchQ =
        !q ||
        e.ticker.toLowerCase().includes(q) ||
        e.name.toLowerCase().includes(q) ||
        e.category.replace("_", " ").includes(q) ||
        e.sector.replace("_", " ").includes(q);
      return matchCat && matchQ;
    });
  }, [etfs, filter, categoryFilter]);

  return (
    <PageTransition>
      <h1 className="text-3xl font-bold mb-2">ETF universe</h1>
      <p className="text-muted-foreground mb-6">
        Curated US ETFs including Shariah-compliant funds — search any ticker for charts
      </p>

      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="flex-1 max-w-md">
          <TickerSearch />
        </div>
        <input
          type="search"
          placeholder="Filter list…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-3 py-2 rounded-lg border border-border bg-background text-sm w-full sm:w-48"
        />
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-3 py-2 rounded-lg border border-border bg-background text-sm"
        >
          {categories.map((c) => (
            <option key={c} value={c}>
              {c === "all" ? "All categories" : c.replace("_", " ")}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="grid md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-20" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <p className="text-muted-foreground text-sm">No ETFs match your filter. Try the search box above.</p>
      ) : (
        <div className="grid md:grid-cols-2 gap-3">
          {filtered.map((etf, i) => (
            <Link key={etf.ticker} to={`/etfs/${etf.ticker}`}>
              <AnimatedCard delay={i * 0.02} className="hover:border-accent/50 transition-colors cursor-pointer">
                <div className="flex justify-between items-center">
                  <div>
                    <span className="font-mono font-semibold text-accent">{etf.ticker}</span>
                    <p className="text-sm text-muted-foreground mt-0.5">{etf.name}</p>
                  </div>
                  <span className="text-xs px-2 py-1 rounded-full bg-muted capitalize">
                    {etf.category.replace("_", " ")}
                  </span>
                </div>
              </AnimatedCard>
            </Link>
          ))}
        </div>
      )}
      <p className="text-xs text-muted-foreground mt-6">
        Showing {filtered.length} of {etfs.length} ETFs
      </p>
    </PageTransition>
  );
}
