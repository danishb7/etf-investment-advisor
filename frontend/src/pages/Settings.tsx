import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Profile } from "@/api/client";
import { PageTransition } from "@/components/ui/PageTransition";
import { AnimatedCard } from "@/components/ui/AnimatedCard";
import { InlineError } from "@/components/ui/InlineError";

export function Settings() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [form, setForm] = useState<Partial<Profile>>({});
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const { data: profile } = useQuery({
    queryKey: ["profile"],
    queryFn: api.getProfile,
  });

  const { data: historyData } = useQuery({
    queryKey: ["recommend-history"],
    queryFn: api.recommendHistory,
  });

  const displayForm = Object.keys(form).length > 0 ? form : profile ?? {};

  const saveMutation = useMutation({
    mutationFn: () => api.updateProfile(displayForm),
    onSuccess: (updated) => {
      queryClient.setQueryData(["profile"], updated);
      queryClient.invalidateQueries({ queryKey: ["recommend"] });
      setForm(updated);
      setSaved(true);
      setError("");
      setTimeout(() => setSaved(false), 2000);
    },
    onError: (e) => setError((e as Error).message),
  });

  const history = historyData?.runs ?? [];

  return (
    <PageTransition>
      <h1 className="text-3xl font-bold mb-8">Settings</h1>

      <InlineError message={error} />

      <AnimatedCard className="mb-6 space-y-4">
        <h2 className="font-semibold">Investor profile</h2>
        {[
          { key: "lump_sum", label: "Lump sum ($)", type: "number" },
          { key: "monthly_sip", label: "Monthly SIP ($)", type: "number" },
          { key: "horizon_months", label: "Horizon (months)", type: "number" },
          { key: "max_expense_ratio", label: "Max expense ratio (%)", type: "number" },
          { key: "exclude_sectors", label: "Exclude sectors", type: "text" },
        ].map(({ key, label, type }) => (
          <label key={key} className="block text-sm">
            {label}
            <input
              type={type}
              className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
              value={String((displayForm as Record<string, unknown>)[key] ?? "")}
              onChange={(e) =>
                setForm({
                  ...displayForm,
                  [key]: type === "number" ? +e.target.value : e.target.value,
                })
              }
            />
          </label>
        ))}
        <label className="block text-sm">
          Risk tolerance
          <select
            className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
            value={displayForm.risk_tolerance ?? "balanced"}
            onChange={(e) => setForm({ ...displayForm, risk_tolerance: e.target.value })}
          >
            <option value="conservative">Conservative</option>
            <option value="balanced">Balanced</option>
            <option value="aggressive">Aggressive</option>
          </select>
        </label>
        <label className="block text-sm">
          Goal
          <select
            className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
            value={displayForm.goal ?? "wealth_building"}
            onChange={(e) => setForm({ ...displayForm, goal: e.target.value })}
          >
            <option value="wealth_building">Wealth building</option>
            <option value="retirement">Retirement</option>
            <option value="education">Education</option>
            <option value="income">Income</option>
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={displayForm.esg_preference ?? false}
            onChange={(e) => setForm({ ...displayForm, esg_preference: e.target.checked })}
          />
          Prefer ESG-focused ETFs (+12 score boost for tagged funds)
        </label>
        <div className="flex gap-3">
          <button
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending}
            className="px-6 py-2 rounded-lg bg-accent text-accent-foreground font-medium disabled:opacity-50"
          >
            {saveMutation.isPending ? "Saving…" : "Save changes"}
          </button>
          {saved && <span className="text-positive text-sm self-center">Saved!</span>}
          <button
            onClick={() => navigate("/onboarding")}
            className="px-4 py-2 rounded-lg bg-muted text-sm"
          >
            Re-run onboarding
          </button>
        </div>
      </AnimatedCard>

      <AnimatedCard>
        <h2 className="font-semibold mb-4">Recommendation history</h2>
        {history.length === 0 ? (
          <p className="text-sm text-muted-foreground">No runs yet</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {history.map((r) => (
              <li key={r.id} className="text-muted-foreground">
                Run #{r.id} — {new Date(r.created_at).toLocaleString()}
              </li>
            ))}
          </ul>
        )}
      </AnimatedCard>
    </PageTransition>
  );
}
