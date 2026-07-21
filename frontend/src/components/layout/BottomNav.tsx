import { Link, useLocation } from "react-router-dom";
import { Compass, FileSpreadsheet, LayoutDashboard, Microscope } from "lucide-react";

export function BottomNav() {
  const location = useLocation();
  const currentPath = location.pathname;

  const items = [
    { path: "/", label: "Dashboard", icon: LayoutDashboard },
    { path: "/discovery", label: "Discover", icon: Compass },
    { path: "/analyse", label: "Analyze", icon: Microscope },
    { path: "/history", label: "Saved", icon: FileSpreadsheet },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-card border-t border-border flex items-center justify-around z-40 shadow-lg px-2 select-none">
      {items.map((item) => {
        const isAnalysisDetail = item.path === "/analyse" && currentPath.startsWith("/analyze/");
        const isActive = item.path === "/" ? currentPath === "/" : currentPath.startsWith(item.path) || isAnalysisDetail;
        const Icon = item.icon;

        return (
          <Link
            key={item.path}
            to={item.path}
            className={`flex flex-col items-center justify-center w-16 h-full gap-0.5 transition-all ${
              isActive ? "text-accent-dark font-black" : "text-muted"
            }`}
          >
            <Icon size={18} className={isActive ? "text-accent-dark scale-110" : "text-muted"} />
            <span className="text-[9px] uppercase tracking-wide font-bold">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
