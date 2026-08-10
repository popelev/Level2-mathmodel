/** Types aligned with contracts/mathmodel/openapi.yaml (draft). */

export type ReadyStatus = {
  ready: boolean;
  level2_reachable?: boolean;
  detail?: string;
};

export type EngineStatus = {
  service: string;
  version: string;
  mode: "scaffold" | "monitoring" | "planning";
  level2_api_url?: string;
  local_var_count?: number;
};

export type LiveTagSummary = {
  tag_id: string;
  device_id?: string;
  value_num?: number | null;
  quality: number;
  time?: string;
};

export type LiveInputsSummary = {
  source: string;
  updated_at: string;
  tag_count?: number;
  tags: LiveTagSummary[];
};

export type LocalVar = {
  id: string;
  name: string;
  value: unknown;
  unit?: string;
  description?: string;
  updated_at?: string;
};

export type LocalVarInput = {
  id: string;
  name: string;
  value?: unknown;
  unit?: string;
  description?: string;
};

export type PlanRequest = {
  horizon_hours?: number;
  notes?: string;
};

export type PlanStub = {
  status: "stub" | "pending" | "ready" | "error";
  message: string;
  requested_at?: string;
  horizon_hours?: number | null;
};

export type TagCatalogEntry = {
  tag_id: string;
  device_id: string;
  path?: string;
  datatype?: string;
  enabled?: boolean;
  writable?: boolean;
  interval_ms?: number;
  node_id?: string;
  last_seen_at?: string;
  raw?: Record<string, unknown>;
};

export type TagBinding = {
  logical_name: string;
  tag_id: string;
  device_id?: string;
  role?: "input" | "output";
  section_id?: string;
  cell_id?: string;
  signal?: string;
};

export type Level2ImportResult = {
  dry_run: boolean;
  devices_seen: number;
  tags_fetched: number;
  inserted: number;
  updated: number;
  total: number;
  preview?: TagCatalogEntry[];
};
