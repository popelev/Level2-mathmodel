import type {
  EngineStatus,
  LiveInputsSummary,
  LocalVar,
  PlanStub,
  ReadyStatus,
} from "./types.js";

export function nowIso(): string {
  return new Date().toISOString();
}

export function createReadyStatus(): ReadyStatus {
  return {
    ready: true,
    level2_reachable: false,
    detail: "BFF mock mode — Level2 not required",
  };
}

export function createEngineStatus(localVarCount: number): EngineStatus {
  return {
    service: "level2-mathmodel",
    version: "0.1.0-draft",
    mode: "scaffold",
    level2_api_url: "http://level2-collector:8080",
    local_var_count: localVarCount,
  };
}

export function createLiveInputs(): LiveInputsSummary {
  const updated_at = nowIso();
  const tags = [
    {
      tag_id: "CELL.01.CURRENT",
      device_id: "rectifier-1",
      value_num: 312.4,
      quality: 0,
      time: updated_at,
    },
    {
      tag_id: "CELL.01.VOLTAGE",
      device_id: "rectifier-1",
      value_num: 0.28,
      quality: 0,
      time: updated_at,
    },
    {
      tag_id: "TANK.A.TEMP",
      device_id: "tank-a",
      value_num: 62.1,
      quality: 0,
      time: updated_at,
    },
    {
      tag_id: "TANK.A.FLOW",
      device_id: "tank-a",
      value_num: null,
      quality: 1,
      time: updated_at,
    },
  ];
  return {
    source: "level2-mock",
    updated_at,
    tag_count: tags.length,
    tags,
  };
}

export function createSeedLocalVars(): LocalVar[] {
  const updated_at = nowIso();
  return [
    {
      id: "target_current",
      name: "Target current",
      value: 320,
      unit: "A",
      description: "Local current setpoint (mock)",
      updated_at,
    },
    {
      id: "efficiency",
      name: "Model efficiency",
      value: 0.92,
      unit: "",
      description: "Computed efficiency (mock)",
      updated_at,
    },
  ];
}

export function createPlanStub(
  partial?: Partial<PlanStub> & { horizon_hours?: number | null },
): PlanStub {
  return {
    status: "stub",
    message: "Planning — Wave 1 stub (mock BFF)",
    requested_at: nowIso(),
    horizon_hours: null,
    ...partial,
  };
}
