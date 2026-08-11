import assert from "node:assert/strict";
import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { describe, test } from "node:test";
import {
  createEngineStatus,
  createLiveInputs,
  createPlanStub,
  createSeedLocalVars,
  createSeedTagCatalog,
} from "./mocks.js";
import { handle } from "./server.js";

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

test("seed tag catalog has stable keys", () => {
  const seed = createSeedTagCatalog();
  assert.ok(seed.length >= 1);
  for (const row of seed) {
    assert.ok(row.tag_id);
    assert.ok(row.device_id);
  }
});

async function withServer(
  fn: (base: string) => Promise<void>,
): Promise<void> {
  const server = createServer((req: IncomingMessage, res: ServerResponse) => {
    void handle(req, res);
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  assert.ok(address && typeof address === "object");
  try {
    await fn(`http://127.0.0.1:${address.port}`);
  } finally {
    await new Promise<void>((resolve, reject) =>
      server.close((err) => (err ? reject(err) : resolve())),
    );
  }
}

describe("HTTP routes (shared mock store)", { concurrency: false }, () => {
  test("healthz responds ok", async () => {
    await withServer(async (base) => {
      const res = await fetch(`${base}/healthz`);
      assert.equal(res.status, 200);
      assert.equal(await res.text(), "ok");
    });
  });

  test("import Level2 tags then list catalog", async () => {
    await withServer(async (base) => {
      const imported = await fetch(`${base}/api/v1/imports/level2/tags`, {
        method: "POST",
      });
      assert.equal(imported.status, 200);
      const counts = (await imported.json()) as {
        inserted: number;
        total: number;
        dry_run: boolean;
      };
      assert.equal(counts.dry_run, false);
      assert.ok(counts.total >= 1);

      const catalogRes = await fetch(`${base}/api/v1/imports/level2/catalog`);
      assert.equal(catalogRes.status, 200);
      const catalog = (await catalogRes.json()) as Array<{
        tag_id: string;
        device_id: string;
        datatype?: string;
        path?: string;
      }>;
      assert.ok(catalog.length >= 1);
      assert.ok(catalog[0]?.tag_id);
      assert.ok(catalog[0]?.device_id);
    });
  });

  test("bindings upsert get delete", async () => {
    await withServer(async (base) => {
      const put = await fetch(`${base}/api/v1/bindings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode: "upsert",
          bindings: [
            {
              logical_name: "cell_current",
              tag_id: "CELL.01.CURRENT",
              device_id: "rectifier-1",
              role: "input",
            },
          ],
        }),
      });
      assert.equal(put.status, 200);
      const afterPut = (await put.json()) as Array<{ logical_name: string }>;
      assert.ok(afterPut.some((b) => b.logical_name === "cell_current"));

      const listed = await fetch(`${base}/api/v1/bindings`);
      assert.equal(listed.status, 200);
      const rows = (await listed.json()) as Array<{ logical_name: string }>;
      assert.ok(rows.some((b) => b.logical_name === "cell_current"));

      const del = await fetch(`${base}/api/v1/bindings/cell_current`, {
        method: "DELETE",
      });
      assert.equal(del.status, 204);
    });
  });
});
