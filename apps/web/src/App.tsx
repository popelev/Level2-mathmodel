import { useState } from "react";
import { ImportPage } from "./pages/ImportPage";
import { LiveInputsPage } from "./pages/LiveInputsPage";
import { LocalVarsPage } from "./pages/LocalVarsPage";
import { PlanPage } from "./pages/PlanPage";
import { StatusPage } from "./pages/StatusPage";

type Tab = "status" | "live" | "locals" | "import" | "plan";

const TABS: { id: Tab; label: string }[] = [
  { id: "status", label: "Status" },
  { id: "live", label: "Live inputs" },
  { id: "locals", label: "Local variables" },
  { id: "import", label: "Import from Level2" },
  { id: "plan", label: "Plan" },
];

export function App() {
  const [tab, setTab] = useState<Tab>("status");

  return (
    <div className="shell">
      <header className="app-header">
        <div>
          <h1>Level2 Mathmodel</h1>
          <p>Mathmodel UI — engine API on this host (port 8090)</p>
        </div>
      </header>

      <nav className="tabs" aria-label="Sections">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={tab === t.id ? "active" : undefined}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "status" && <StatusPage />}
      {tab === "live" && <LiveInputsPage />}
      {tab === "locals" && <LocalVarsPage />}
      {tab === "import" && <ImportPage />}
      {tab === "plan" && <PlanPage />}
    </div>
  );
}
