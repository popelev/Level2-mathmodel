import { useEffect, useState } from "react";
import { api } from "../api";
import type { EngineStatus, ReadyStatus, RecalcStatus } from "../types";

type ConnState = "loading" | "ok" | "error";

export function StatusPage() {
  const [conn, setConn] = useState<ConnState>("loading");
  const [health, setHealth] = useState<string>("");
  const [ready, setReady] = useState<ReadyStatus | null>(null);
  const [status, setStatus] = useState<EngineStatus | null>(null);
  const [recalc, setRecalc] = useState<RecalcStatus | null>(null);
  const [error, setError] = useState<string>("");

  async function load() {
    setConn("loading");
    setError("");
    try {
      const [hz, rz, st, rc] = await Promise.all([
        api.healthz(),
        api.readyz(),
        api.status(),
        api.recalcStatus().catch(() => null),
      ]);
      setHealth(typeof hz === "string" ? hz : "ok");
      setReady(rz);
      setStatus(st);
      setRecalc(rc);
      setConn("ok");
    } catch (e) {
      setConn("error");
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const lastTrigger =
    status?.recalc_last_trigger_at ??
    recalc?.triggers?.find((t) => t.state?.last_trigger_at)?.state
      ?.last_trigger_at ??
    null;

  let lastResult = "—";
  if (status?.recalc_last_error) {
    lastResult = `error: ${status.recalc_last_error}`;
  } else if (status?.recalc_last_ok_at) {
    lastResult = `ok @ ${status.recalc_last_ok_at}`;
  } else if (recalc?.triggers?.length) {
    const fired = [...recalc.triggers]
      .reverse()
      .find((t) => t.state?.last_result === "ok" || t.state?.last_result === "error");
    if (fired?.state?.last_result === "error") {
      lastResult = `error: ${fired.state.last_error ?? "unknown"}`;
    } else if (fired?.state?.last_result === "ok") {
      lastResult = `ok (${fired.trigger_id})`;
    }
  }

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
          {conn === "ok" && "engine reachable"}
          {conn === "error" && "no connection to engine"}
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

      <h3 style={{ marginTop: "1.5rem" }}>Recalc poll</h3>
      <p className="lead">
        Multi-trigger flag polling (`GET /api/v1/recalc/status`). Handlers write
        local vars only.
      </p>
      <div className="meta-grid">
        <div className="meta">
          <span className="label">poll enabled</span>
          <span className="value">
            {status?.recalc_poll_enabled === undefined
              ? "—"
              : status.recalc_poll_enabled
                ? "yes"
                : "no"}
          </span>
        </div>
        <div className="meta">
          <span className="label">poll running</span>
          <span className="value">
            {status?.recalc_poll_running === undefined
              ? "—"
              : status.recalc_poll_running
                ? "yes"
                : "no"}
          </span>
        </div>
        <div className="meta">
          <span className="label">triggers</span>
          <span className="value">
            {status?.recalc_trigger_count ?? recalc?.trigger_count ?? "—"}
          </span>
        </div>
        <div className="meta">
          <span className="label">last trigger</span>
          <span className="value">{lastTrigger ?? "—"}</span>
        </div>
        <div className="meta">
          <span className="label">last recalc</span>
          <span className="value">{lastResult}</span>
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
