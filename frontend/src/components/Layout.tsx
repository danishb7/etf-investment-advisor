import { NavLink, Outlet } from "react-router-dom";
import { BarChart3, Home, PieChart, Settings, Wallet, LineChart } from "lucide-react";
import { ThemeToggle } from "./ui/ThemeToggle";
import { Disclaimer } from "./Disclaimer";
import { TickerSearch } from "./TickerSearch";

const nav = [
  { to: "/", icon: Home, label: "Dashboard" },
  { to: "/etfs", icon: BarChart3, label: "ETFs" },
  { to: "/simulate", icon: LineChart, label: "Simulate" },
  { to: "/portfolio", icon: Wallet, label: "Portfolio" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-50 border-b border-border/50 bg-card/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <PieChart className="text-accent" size={22} />
            <span className="font-semibold text-lg">ETF Advisor</span>
          </div>
          <nav className="hidden md:flex items-center gap-1">
            {nav.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                    isActive ? "bg-accent text-accent-foreground" : "hover:bg-muted text-muted-foreground"
                  }`
                }
              >
                <Icon size={16} />
                {label}
              </NavLink>
            ))}
          </nav>
          <div className="hidden md:block">
            <TickerSearch compact />
          </div>
          <ThemeToggle />
        </div>
        <div className="md:hidden px-4 pb-3">
          <TickerSearch />
        </div>
        <nav className="md:hidden flex overflow-x-auto gap-1 px-4 pb-2">
          {nav.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `shrink-0 px-3 py-1 rounded-full text-xs ${
                  isActive ? "bg-accent text-accent-foreground" : "bg-muted text-muted-foreground"
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-8">
        <Outlet />
      </main>
      <footer className="max-w-6xl mx-auto w-full px-4 pb-8">
        <Disclaimer />
      </footer>
    </div>
  );
}
