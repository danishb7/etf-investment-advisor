import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search } from "lucide-react";
import { api } from "@/api/client";

type SearchResult = {
  ticker: string;
  name: string;
  category?: string;
  in_universe?: boolean;
  has_data?: boolean;
};

export function TickerSearch({ compact = false }: { compact?: boolean }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (query.trim().length < 1) {
      setResults([]);
      return;
    }
    const t = setTimeout(async () => {
      setLoading(true);
      try {
        const r = await api.searchEtfs(query.trim());
        const items: SearchResult[] = r.curated.map((e) => ({
          ticker: e.ticker,
          name: e.name,
          category: e.category,
          in_universe: true,
        }));
        if (r.lookup && !items.some((i) => i.ticker === r.lookup!.ticker)) {
          items.unshift({
            ticker: r.lookup.ticker,
            name: r.lookup.name,
            category: r.lookup.category,
            in_universe: r.lookup.in_universe,
            has_data: r.lookup.has_data,
          });
        }
        setResults(items.slice(0, 8));
        setOpen(true);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(t);
  }, [query]);

  const go = (ticker: string) => {
    setQuery("");
    setOpen(false);
    navigate(`/etfs/${ticker}`);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && query.trim()) {
      go(query.trim().toUpperCase());
    }
    if (e.key === "Escape") setOpen(false);
  };

  return (
    <div className={`relative ${compact ? "w-full max-w-xs" : "w-full max-w-md"}`}>
      <div className="relative">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none"
        />
        <input
          type="search"
          placeholder="Search ticker (e.g. SPUS, HLAL)…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query && setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          onKeyDown={onKeyDown}
          className="w-full pl-9 pr-3 py-2 rounded-lg border border-border bg-background text-sm font-mono placeholder:font-sans placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/40"
          aria-label="Search ETF ticker"
        />
      </div>
      {open && (results.length > 0 || loading) && (
        <ul className="absolute z-50 mt-1 w-full rounded-lg border border-border bg-card shadow-lg overflow-hidden">
          {loading && (
            <li className="px-3 py-2 text-sm text-muted-foreground">Searching…</li>
          )}
          {results.map((r) => (
            <li key={r.ticker}>
              <button
                type="button"
                className="w-full text-left px-3 py-2 hover:bg-muted transition-colors flex justify-between gap-2"
                onMouseDown={() => go(r.ticker)}
              >
                <span>
                  <span className="font-mono font-semibold text-accent">{r.ticker}</span>
                  <span className="block text-xs text-muted-foreground truncate max-w-[240px]">{r.name}</span>
                </span>
                {r.in_universe === false && (
                  <span className="text-xs text-muted-foreground shrink-0">lookup</span>
                )}
              </button>
            </li>
          ))}
          {!loading && query && results.length === 0 && (
            <li className="px-3 py-2 text-sm text-muted-foreground">
              No results — press Enter to try {query}
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
