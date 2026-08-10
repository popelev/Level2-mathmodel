import type {
  EngineStatus,
  Level2ImportResult,
  LiveInputsSummary,
  LocalVar,
  LocalVarInput,
  PlanStub,
  ReadyStatus,
  TagBinding,
  TagCatalogEntry,
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
    let detail = text;
    try {
      const parsed = JSON.parse(text) as { detail?: string; error?: string };
      if (parsed.detail || parsed.error) {
        detail = [parsed.error, parsed.detail].filter(Boolean).join(": ");
      }
    } catch {
      /* keep raw text */
    }
    throw new Error(
      `${res.status} ${res.statusText}${detail ? `: ${detail}` : ""}`,
    );
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

/**
 * Client for mathmodel OpenAPI routes served by the FastAPI engine
 * (lab image on :8090). Paths must match `services/engine` — not mock-only BFF extras.
 */
export const api = {
  healthz: () => request<string>("/healthz"),
  readyz: () => request<ReadyStatus>("/readyz"),
  status: () => request<EngineStatus>("/api/v1/status"),
  /** Engine: GET /api/v1/live/inputs (Level2 read-only projection). */
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
  importLevel2Tags: () =>
    request<Level2ImportResult>("/api/v1/imports/level2/tags", {
      method: "POST",
    }),
  listTagCatalog: () =>
    request<TagCatalogEntry[]>("/api/v1/imports/level2/catalog"),
  listBindings: () => request<TagBinding[]>("/api/v1/bindings"),
  upsertBindings: (bindings: TagBinding[]) =>
    request<TagBinding[]>("/api/v1/bindings", {
      method: "PUT",
      body: JSON.stringify({ mode: "upsert", bindings }),
    }),
  deleteBinding: (logicalName: string) =>
    request<void>(`/api/v1/bindings/${encodeURIComponent(logicalName)}`, {
      method: "DELETE",
    }),
};
