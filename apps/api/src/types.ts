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
