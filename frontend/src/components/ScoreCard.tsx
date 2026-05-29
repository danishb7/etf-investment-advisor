import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import type { ETFRecommendation } from "@/api/client";
import { AnimatedCard } from "./ui/AnimatedCard";

function BreakdownBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{label}</span>
        <span>{value.toFixed(0)}</span>
      </div>
      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
        <motion.div
          className="h-full bg-accent rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

export function ScoreCard({ etf, index = 0 }: { etf: ETFRecommendation; index?: number }) {
  const bd = etf.breakdown;
  return (
    <AnimatedCard delay={index * 0.05}>
      <div className="flex justify-between items-start mb-3">
        <div>
          <Link to={`/etfs/${etf.ticker}`} className="font-semibold text-lg hover:text-accent transition-colors">
            {etf.ticker}
          </Link>
          <p className="text-sm text-muted-foreground">{etf.name}</p>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold text-accent">{etf.allocation_pct}%</span>
          <p className="text-xs text-muted-foreground">allocation</p>
        </div>
      </div>
      <p className="text-sm mb-4 leading-relaxed">{etf.explanation}</p>
      <div className="grid grid-cols-2 gap-3 mb-3">
        <BreakdownBar label="Momentum" value={bd.momentum} />
        <BreakdownBar label="Sharpe" value={bd.sharpe} />
        <BreakdownBar label="Volatility fit" value={bd.volatility} />
        <BreakdownBar label="Expense" value={bd.expense} />
        <BreakdownBar label="Macro fit" value={bd.macro_fit} />
        <BreakdownBar label="Sentiment" value={bd.sentiment} />
        {(bd.esg_fit ?? 0) > 0 && <BreakdownBar label="ESG boost" value={bd.esg_fit!} />}
        {(bd.shariah_fit ?? 0) > 0 && <BreakdownBar label="Shariah boost" value={bd.shariah_fit!} />}
      </div>
      <div className="flex flex-wrap gap-2 text-xs">
        <span className="px-2 py-0.5 rounded-full bg-muted">Score {etf.final_score.toFixed(0)}</span>
        {etf.expense_ratio != null && (
          <span className="px-2 py-0.5 rounded-full bg-muted">
            ER {(etf.expense_ratio * 100).toFixed(2)}%
          </span>
        )}
        {etf.return_1y != null && (
          <span className={`px-2 py-0.5 rounded-full ${etf.return_1y >= 0 ? "text-positive" : "text-negative"} bg-muted`}>
            1Y {etf.return_1y > 0 ? "+" : ""}
            {etf.return_1y.toFixed(1)}%
          </span>
        )}
      </div>
      {etf.risk_warning && (
        <p className="mt-3 text-xs text-negative/90 border-t border-border/50 pt-3">{etf.risk_warning}</p>
      )}
    </AnimatedCard>
  );
}
