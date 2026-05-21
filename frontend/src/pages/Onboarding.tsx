import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/api/client";
import { PageTransition } from "@/components/ui/PageTransition";

const STEPS = [
  {
    title: "Your budget",
    fields: ["lump_sum", "monthly_sip"] as const,
  },
  {
    title: "Time horizon",
    fields: ["horizon_months"] as const,
  },
  {
    title: "Risk & goals",
    fields: ["risk_tolerance", "goal"] as const,
  },
  {
    title: "Preferences",
    fields: ["max_expense_ratio", "exclude_sectors"] as const,
  },
];

export function Onboarding() {
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    lump_sum: 5000,
    monthly_sip: 200,
    horizon_months: 60,
    risk_tolerance: "balanced",
    goal: "wealth_building",
    tax_bracket: "",
    max_expense_ratio: 0.5,
    exclude_sectors: "",
    esg_preference: false,
  });

  const submit = async () => {
    setLoading(true);
    try {
      await api.updateProfile({ ...form, onboarding_complete: true });
      await api.prefetch().catch(() => {});
      window.location.href = "/";
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const current = STEPS[step];

  return (
    <PageTransition>
      <div className="max-w-lg mx-auto">
        <h1 className="text-3xl font-bold mb-2">Welcome</h1>
        <p className="text-muted-foreground mb-8">Let&apos;s set up your investor profile in a few steps.</p>

        <div className="flex gap-2 mb-8">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className={`h-1.5 flex-1 rounded-full transition-colors ${
                i <= step ? "bg-accent" : "bg-muted"
              }`}
            />
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
            className="bg-card rounded-xl border border-border/50 p-6 shadow-sm space-y-4"
          >
            <h2 className="text-xl font-semibold">{current.title}</h2>

            {step === 0 && (
              <>
                <label className="block text-sm">
                  Lump sum ($)
                  <input
                    type="number"
                    className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
                    value={form.lump_sum}
                    onChange={(e) => setForm({ ...form, lump_sum: +e.target.value })}
                  />
                </label>
                <label className="block text-sm">
                  Monthly SIP ($)
                  <input
                    type="number"
                    className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
                    value={form.monthly_sip}
                    onChange={(e) => setForm({ ...form, monthly_sip: +e.target.value })}
                  />
                </label>
              </>
            )}

            {step === 1 && (
              <label className="block text-sm">
                Investment horizon
                <select
                  className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
                  value={form.horizon_months}
                  onChange={(e) => setForm({ ...form, horizon_months: +e.target.value })}
                >
                  <option value={6}>6 months</option>
                  <option value={12}>1 year</option>
                  <option value={36}>3 years</option>
                  <option value={60}>5 years</option>
                  <option value={120}>10+ years</option>
                </select>
              </label>
            )}

            {step === 2 && (
              <>
                <label className="block text-sm">
                  Risk tolerance
                  <select
                    className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
                    value={form.risk_tolerance}
                    onChange={(e) => setForm({ ...form, risk_tolerance: e.target.value })}
                  >
                    <option value="conservative">Conservative</option>
                    <option value="balanced">Balanced</option>
                    <option value="aggressive">Aggressive</option>
                  </select>
                </label>
                <label className="block text-sm">
                  Primary goal
                  <select
                    className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
                    value={form.goal}
                    onChange={(e) => setForm({ ...form, goal: e.target.value })}
                  >
                    <option value="wealth_building">Wealth building</option>
                    <option value="retirement">Retirement</option>
                    <option value="education">Education fund</option>
                    <option value="income">Income</option>
                  </select>
                </label>
              </>
            )}

            {step === 3 && (
              <>
                <label className="block text-sm">
                  Max expense ratio (%)
                  <input
                    type="number"
                    step="0.05"
                    className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
                    value={form.max_expense_ratio}
                    onChange={(e) => setForm({ ...form, max_expense_ratio: +e.target.value })}
                  />
                </label>
                <label className="block text-sm">
                  Exclude sectors (comma-separated)
                  <input
                    type="text"
                    placeholder="e.g. energy, gold"
                    className="mt-1 w-full px-3 py-2 rounded-lg border border-border bg-background"
                    value={form.exclude_sectors}
                    onChange={(e) => setForm({ ...form, exclude_sectors: e.target.value })}
                  />
                </label>
              </>
            )}
          </motion.div>
        </AnimatePresence>

        <div className="flex justify-between mt-6">
          <button
            className="px-4 py-2 rounded-lg text-muted-foreground hover:bg-muted disabled:opacity-40"
            disabled={step === 0}
            onClick={() => setStep((s) => s - 1)}
          >
            Back
          </button>
          {step < STEPS.length - 1 ? (
            <button
              className="px-6 py-2 rounded-lg bg-accent text-accent-foreground font-medium hover:opacity-90 transition-opacity"
              onClick={() => setStep((s) => s + 1)}
            >
              Continue
            </button>
          ) : (
            <button
              className="px-6 py-2 rounded-lg bg-accent text-accent-foreground font-medium hover:opacity-90 disabled:opacity-50"
              onClick={submit}
              disabled={loading}
            >
              {loading ? "Saving…" : "Get recommendations"}
            </button>
          )}
        </div>
      </div>
    </PageTransition>
  );
}
