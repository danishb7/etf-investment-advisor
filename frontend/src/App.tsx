import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { api } from "@/api/client";
import { Layout } from "@/components/Layout";
import { ThemeProvider } from "@/components/ui/ThemeProvider";
import { Dashboard } from "@/pages/Dashboard";
import { ETFDetail } from "@/pages/ETFDetail";
import { ETFList } from "@/pages/ETFList";
import { Onboarding } from "@/pages/Onboarding";
import { PortfolioPage } from "@/pages/Portfolio";
import { Settings } from "@/pages/Settings";
import { Simulate } from "@/pages/Simulate";

function AppRoutes() {
  const [ready, setReady] = useState(false);
  const [onboarded, setOnboarded] = useState(false);

  useEffect(() => {
    api
      .getProfile()
      .then((p) => {
        setOnboarded(p.onboarding_complete);
        setReady(true);
      })
      .catch(() => setReady(true));
  }, []);

  if (!ready) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="skeleton w-48 h-8 rounded-lg" />
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/onboarding" element={<Onboarding />} />
      <Route
        path="/"
        element={onboarded ? <Layout /> : <Navigate to="/onboarding" replace />}
      >
        <Route index element={<Dashboard />} />
        <Route path="etfs" element={<ETFList />} />
        <Route path="etfs/:ticker" element={<ETFDetail />} />
        <Route path="simulate" element={<Simulate />} />
        <Route path="portfolio" element={<PortfolioPage />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to={onboarded ? "/" : "/onboarding"} replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </ThemeProvider>
  );
}
