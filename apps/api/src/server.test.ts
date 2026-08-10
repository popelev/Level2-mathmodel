import assert from "node:assert/strict";
import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { test } from "node:test";
import {
  createEngineStatus,
  createLiveInputs,
  createPlanStub,
  createSeedLocalVars,
} from "./mocks.js";

test("seed local vars have required fields", () => {
  const vars = createSeedLocalVars();
  assert.ok(vars.length >= 1);
  for (const v of vars) {
    assert.equal(typeof v.id, "string");
    assert.equal(typeof v.name, "string");
    assert.ok("value" in v);
  }
});

test("engine status mock matches OpenAPI shape", () => {
  const status = createEngineStatus(2);
  assert.equal(status.service, "level2-mathmodel");
  assert.equal(status.mode, "scaffold");
  assert.equal(status.local_var_count, 2);
});

test("live inputs mock includes tags", () => {
  const live = createLiveInputs();
  assert.equal(live.source, "level2-mock");
  assert.ok(Array.isArray(live.tags));
  assert.ok((live.tag_count ?? 0) > 0);
});

test("plan stub defaults", () => {
  const plan = createPlanStub();
  assert.equal(plan.status, "stub");
  assert.ok(plan.message.length > 0);
});

test("healthz responds ok via tiny listener", async () => {
  const server = createServer((req: IncomingMessage, res: ServerResponse) => {
    if (req.url === "/healthz") {
      res.writeHead(200, { "Content-Type": "text/plain" });
      res.end("ok");
      return;
    }
    res.writeHead(404);
    res.end();
  });

  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  assert.ok(address && typeof address === "object");
  const res = await fetch(`http://127.0.0.1:${address.port}/healthz`);
  assert.equal(res.status, 200);
  assert.equal(await res.text(), "ok");
  await new Promise<void>((resolve, reject) =>
    server.close((err) => (err ? reject(err) : resolve())),
  );
});
