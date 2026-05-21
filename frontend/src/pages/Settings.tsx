import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type Profile } from "@/api/client";
import { PageTransition } from "@/components/ui/PageTransition";
import { AnimatedCard } from "@/components/ui/AnimatedCard";

export function Settings() {
  const navigate = useNavigate();
  const [form, setForm] = useState<Partial<Profile>>({});
  const [history, setHistory] = useState<{ id: number; created_at: string }[]>([]);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.getProfile().then(setForm);
    api.recommendHistory().then((r) => setHistory(r.runs));
  }, []);

  const save = async () => {
    await api.updateProfile(form);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <PageTransition>
      <h1 className="text-3xl font-bold mb-8">Settings</h1>

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
              value={String((form as Record<string, unknown>)[key] ?? "")}
              onChange={(e) =>
                setForm({
                  ...form,
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
            value={form.risk_tolerance ?? "balanced"}
            onChange={(e) => setForm({ ...form, risk_tolerance: e.target.value })}
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
            value={form.goal ?? "wealth_building"}
            onChange={(e) => setForm({ ...form, goal: e.target.value })}
          >
            <option value="wealth_building">Wealth building</option>
            <option value="retirement">Retirement</option>
            <option value="education">Education</option>
            <option value="income">Income</option>
          </select>
        </label>
        <div className="flex gap-3">
          <button onClick={save} className="px-6 py-2 rounded-lg bg-accent text-accent-foreground font-medium">
            Save changes
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
