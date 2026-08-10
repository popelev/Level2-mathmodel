/**
 * Mock BFF implementing contracts/mathmodel/openapi.yaml (Wave 1).
 * Does not call live engine / Level2 — in-memory mocks only.
 */
import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import {
  createEngineStatus,
  createLiveInputs,
  createPlanStub,
  createReadyStatus,
  createSeedLocalVars,
  nowIso,
} from "./mocks.js";
import type { LocalVar, LocalVarInput, PlanRequest, PlanStub } from "./types.js";

const PORT = Number(process.env.PORT ?? process.env.MATHMODEL_PORT ?? 8090);
const HOST = process.env.HOST ?? "127.0.0.1";

const localVars = new Map<string, LocalVar>(
  createSeedLocalVars().map((v) => [v.id, v]),
);
let plan: PlanStub = createPlanStub();

function send(
  res: ServerResponse,
  status: number,
  body: unknown,
  contentType = "application/json; charset=utf-8",
): void {
  const payload =
    contentType.startsWith("application/json") && typeof body !== "string"
      ? JSON.stringify(body)
      : String(body);
  res.writeHead(status, {
    "Content-Type": contentType,
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  });
  res.end(payload);
}

function notFound(res: ServerResponse): void {
  send(res, 404, { error: "not_found" });
}

async function readJson<T>(req: IncomingMessage): Promise<T> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  const raw = Buffer.concat(chunks).toString("utf8").trim();
  if (!raw) {
    return {} as T;
  }
  return JSON.parse(raw) as T;
}

function parseLocalVarInput(body: LocalVarInput): LocalVar | null {
  if (!body || typeof body.id !== "string" || typeof body.name !== "string") {
    return null;
  }
  if (!body.id.trim() || !body.name.trim()) {
    return null;
  }
  return {
    id: body.id.trim(),
    name: body.name.trim(),
    value: body.value ?? null,
    unit: body.unit,
    description: body.description,
    updated_at: nowIso(),
  };
}

async function handle(
  req: IncomingMessage,
  res: ServerResponse,
): Promise<void> {
  const method = req.method ?? "GET";
  const url = new URL(req.url ?? "/", `http://${HOST}:${PORT}`);
  const path = url.pathname;

  if (method === "OPTIONS") {
    send(res, 204, "");
    return;
  }

  if (method === "GET" && path === "/healthz") {
    send(res, 200, "ok", "text/plain; charset=utf-8");
    return;
  }

  if (method === "GET" && path === "/readyz") {
    send(res, 200, createReadyStatus());
    return;
  }

  if (method === "GET" && path === "/api/v1/status") {
    send(res, 200, createEngineStatus(localVars.size));
    return;
  }

  if (method === "GET" && path === "/api/v1/live/inputs") {
    send(res, 200, createLiveInputs());
    return;
  }

  if (path === "/api/v1/local-vars") {
    if (method === "GET") {
      send(res, 200, Array.from(localVars.values()));
      return;
    }
    if (method === "POST") {
      let body: LocalVarInput;
      try {
        body = await readJson<LocalVarInput>(req);
      } catch {
        send(res, 400, { error: "invalid_json" });
        return;
      }
      const created = parseLocalVarInput(body);
      if (!created) {
        send(res, 400, { error: "invalid_body" });
        return;
      }
      if (localVars.has(created.id)) {
        send(res, 409, { error: "id_exists" });
        return;
      }
      localVars.set(created.id, created);
      send(res, 201, created);
      return;
    }
  }

  const localVarMatch = path.match(/^\/api\/v1\/local-vars\/([^/]+)$/);
  if (localVarMatch) {
    const id = decodeURIComponent(localVarMatch[1]!);
    if (method === "GET") {
      const item = localVars.get(id);
      if (!item) {
        notFound(res);
        return;
      }
      send(res, 200, item);
      return;
    }
    if (method === "PUT") {
      if (!localVars.has(id)) {
        notFound(res);
        return;
      }
      let body: LocalVarInput;
      try {
        body = await readJson<LocalVarInput>(req);
      } catch {
        send(res, 400, { error: "invalid_json" });
        return;
      }
      const updated = parseLocalVarInput({ ...body, id });
      if (!updated) {
        send(res, 400, { error: "invalid_body" });
        return;
      }
      localVars.set(id, updated);
      send(res, 200, updated);
      return;
    }
    if (method === "DELETE") {
      if (!localVars.has(id)) {
        notFound(res);
        return;
      }
      localVars.delete(id);
      send(res, 204, "");
      return;
    }
  }

  if (path === "/api/v1/plan") {
    if (method === "GET") {
      send(res, 200, plan);
      return;
    }
    if (method === "POST") {
      let body: PlanRequest = {};
      try {
        body = await readJson<PlanRequest>(req);
      } catch {
        send(res, 400, { error: "invalid_json" });
        return;
      }
      plan = createPlanStub({
        status: "stub",
        message: body.notes?.trim()
          ? `Request accepted (stub): ${body.notes.trim()}`
          : "Planning request accepted (stub, mock BFF)",
        horizon_hours: body.horizon_hours ?? null,
        requested_at: nowIso(),
      });
      send(res, 202, plan);
      return;
    }
  }

  notFound(res);
}

export function startServer(): void {
  const server = createServer((req, res) => {
    void handle(req, res).catch((err: unknown) => {
      console.error(err);
      send(res, 500, { error: "internal_error" });
    });
  });

  server.listen(PORT, HOST, () => {
    console.log(`mathmodel mock BFF listening on http://${HOST}:${PORT}`);
  });
}
