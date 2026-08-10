import { useEffect, useState } from "react";
import { api } from "../api";
import type { EngineStatus, ReadyStatus } from "../types";

type ConnState = "loading" | "ok" | "error";

export function StatusPage() {
  const [conn, setConn] = useState<ConnState>("loading");
  const [health, setHealth] = useState<string>("");
  const [ready, setReady] = useState<ReadyStatus | null>(null);
  const [status, setStatus] = useState<EngineStatus | null>(null);
  const [error, setError] = useState<string>("");

  async function load() {
    setConn("loading");
    setError("");
    try {
      const [hz, rz, st] = await Promise.all([
        api.healthz(),
        api.readyz(),
        api.status(),
      ]);
      setHealth(typeof hz === "string" ? hz : "ok");
      setReady(rz);
      setStatus(st);
      setConn("ok");
    } catch (e) {
      setConn("error");
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <section className="panel">
      <h2>Connection status</h2>
      <p className="lead">
        Checking engine OpenAPI (`/healthz`, `/readyz`, `/api/v1/status`).
      </p>

      <div className="toolbar">
        <button type="button" className="primary" onClick={() => void load()}>
          Refresh
        </button>
        <span
          className={`badge ${conn === "ok" ? "ok" : conn === "error" ? "bad" : "warn"}`}
        >
          {conn === "loading" && "checking…"}
          {conn === "ok" && "BFF reachable"}
          {conn === "error" && "no connection to BFF"}
        </span>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="meta-grid">
        <div className="meta">
          <span className="label">healthz</span>
          <span className="value">{health || "—"}</span>
        </div>
        <div className="meta">
          <span className="label">ready</span>
          <span className="value">
            {ready ? (ready.ready ? "true" : "false") : "—"}
          </span>
        </div>
        <div className="meta">
          <span className="label">Level2 reachable</span>
          <span className="value">
            {ready?.level2_reachable === undefined
              ? "—"
              : ready.level2_reachable
                ? "yes"
                : "no (expected in mock)"}
          </span>
        </div>
        <div className="meta">
          <span className="label">service</span>
          <span className="value">{status?.service ?? "—"}</span>
        </div>
        <div className="meta">
          <span className="label">version</span>
          <span className="value">{status?.version ?? "—"}</span>
        </div>
        <div className="meta">
          <span className="label">mode</span>
          <span className="value">{status?.mode ?? "—"}</span>
        </div>
        <div className="meta">
          <span className="label">local variables</span>
          <span className="value">
            {status?.local_var_count ?? "—"}
          </span>
        </div>
      </div>

      {ready?.detail && (
        <p className="muted" style={{ marginTop: "1rem" }}>
          {ready.detail}
        </p>
      )}
    </section>
  );
}
