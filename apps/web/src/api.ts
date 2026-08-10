import type {
  EngineStatus,
  LiveInputsSummary,
  LocalVar,
  LocalVarInput,
  PlanStub,
  ReadyStatus,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
    },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  const ct = res.headers.get("content-type") ?? "";
  if (ct.includes("application/json")) {
    return (await res.json()) as T;
  }
  return (await res.text()) as T;
}

export const api = {
  healthz: () => request<string>("/healthz"),
  readyz: () => request<ReadyStatus>("/readyz"),
  status: () => request<EngineStatus>("/api/v1/status"),
  liveInputs: () => request<LiveInputsSummary>("/api/v1/live/inputs"),
  listLocalVars: () => request<LocalVar[]>("/api/v1/local-vars"),
  updateLocalVar: (id: string, body: LocalVarInput) =>
    request<LocalVar>(`/api/v1/local-vars/${encodeURIComponent(id)}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  getPlan: () => request<PlanStub>("/api/v1/plan"),
  requestPlan: (horizon_hours: number, notes?: string) =>
    request<PlanStub>("/api/v1/plan", {
      method: "POST",
      body: JSON.stringify({ horizon_hours, notes }),
    }),
};
