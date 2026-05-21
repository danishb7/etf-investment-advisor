import { AlertCircle } from "lucide-react";

export function Disclaimer() {
  return (
    <div className="flex gap-3 p-4 rounded-lg bg-muted/60 border border-border/50 text-sm text-muted-foreground">
      <AlertCircle className="shrink-0 text-accent mt-0.5" size={18} />
      <p>
        This app provides <strong className="text-foreground font-medium">educational information only</strong> and is
        not licensed financial advice. Past performance does not guarantee future results. Consult a qualified
        advisor before investing.
      </p>
    </div>
  );
}
