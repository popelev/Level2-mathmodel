import { useEffect, useState } from "react";
import { api } from "../api";
import type { PlanStub } from "../types";

export function PlanPage() {
  const [plan, setPlan] = useState<PlanStub | null>(null);
  const [horizon, setHorizon] = useState(8);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    setError("");
    try {
      setPlan(await api.getPlan());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function requestPlan() {
    setBusy(true);
    setError("");
    try {
      setPlan(await api.requestPlan(horizon, notes || undefined));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <section className="panel">
      <h2>Plan (stub)</h2>
      <p className="lead">
        Wave 1: stub endpoint `/api/v1/plan`. Real calculation comes in later waves.
      </p>

      <div className="toolbar">
        <button type="button" className="secondary" onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {plan && (
        <div className="meta-grid" style={{ marginBottom: "1rem" }}>
          <div className="meta">
            <span className="label">status</span>
            <span className="value">{plan.status}</span>
          </div>
          <div className="meta">
            <span className="label">horizon, h</span>
            <span className="value">
              {plan.horizon_hours ?? "—"}
            </span>
          </div>
          <div className="meta">
            <span className="label">requested_at</span>
            <span className="value">{plan.requested_at ?? "—"}</span>
          </div>
          <div className="meta">
            <span className="label">message</span>
            <span className="value">{plan.message}</span>
          </div>
        </div>
      )}

      <div className="form-grid">
        <label>
          Planning horizon (hours)
          <input
            type="number"
            min={1}
            step={1}
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
          />
        </label>
        <label>
          Notes
          <textarea
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="optional"
          />
        </label>
        <div className="toolbar">
          <button
            type="button"
            className="primary"
            disabled={busy}
            onClick={() => void requestPlan()}
          >
            {busy ? "Requesting…" : "Request plan (stub)"}
          </button>
        </div>
      </div>
    </section>
  );
}
