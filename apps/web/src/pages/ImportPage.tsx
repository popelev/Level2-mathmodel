import { useEffect, useState, type FormEvent } from "react";
import { api } from "../api";
import type { TagBinding, TagCatalogEntry } from "../types";

export function ImportPage() {
  const [catalog, setCatalog] = useState<TagCatalogEntry[]>([]);
  const [bindings, setBindings] = useState<TagBinding[]>([]);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [busy, setBusy] = useState(false);

  const [logicalName, setLogicalName] = useState("");
  const [tagId, setTagId] = useState("");
  const [deviceId, setDeviceId] = useState("");
  const [role, setRole] = useState<"input" | "output">("input");

  async function refresh() {
    setError("");
    try {
      const [cat, binds] = await Promise.all([
        api.listTagCatalog(),
        api.listBindings(),
      ]);
      setCatalog(cat);
      setBindings(binds);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function importTags() {
    setBusy(true);
    setError("");
    setInfo("");
    try {
      const result = await api.importLevel2Tags();
      setInfo(
        `Imported: inserted=${result.inserted}, updated=${result.updated}, total=${result.total}`,
      );
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  function pickCatalogRow(row: TagCatalogEntry) {
    setTagId(row.tag_id);
    setDeviceId(row.device_id);
  }

  async function saveBinding(ev: FormEvent) {
    ev.preventDefault();
    if (!logicalName.trim() || !tagId.trim()) return;
    setBusy(true);
    setError("");
    try {
      await api.upsertBindings([
        {
          logical_name: logicalName.trim(),
          tag_id: tagId.trim(),
          device_id: deviceId.trim() || undefined,
          role,
        },
      ]);
      setLogicalName("");
      setTagId("");
      setDeviceId("");
      setRole("input");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function removeBinding(name: string) {
    setBusy(true);
    setError("");
    try {
      await api.deleteBinding(name);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <section className="panel">
      <h2>Import from Level2</h2>
      <p className="lead">
        Read-only catalog import via mathmodel API (
        <code>POST /api/v1/imports/level2/tags</code>). Bindings map{" "}
        <code>logical_name</code> → stable <code>tag_id</code>. Model outputs
        stay in local variables.
      </p>

      <div className="toolbar">
        <button
          type="button"
          className="primary"
          disabled={busy}
          onClick={() => void importTags()}
        >
          {busy ? "Working…" : "Import from Level2"}
        </button>
        <button
          type="button"
          className="secondary"
          disabled={busy}
          onClick={() => void refresh()}
        >
          Refresh
        </button>
      </div>

      {info && <p className="ok">{info}</p>}
      {error && <p className="error">{error}</p>}

      <h3 style={{ marginTop: "1.25rem" }}>Tag catalog</h3>
      <p className="muted">
        Click a row to fill the binding form. Columns: tag_id, device_id,
        datatype, path.
      </p>
      <table className="data">
        <thead>
          <tr>
            <th>tag_id</th>
            <th>device_id</th>
            <th>datatype</th>
            <th>path</th>
          </tr>
        </thead>
        <tbody>
          {catalog.length === 0 && (
            <tr>
              <td colSpan={4}>No catalog entries yet. Run Import from Level2.</td>
            </tr>
          )}
          {catalog.map((row) => (
            <tr
              key={`${row.device_id}:${row.tag_id}`}
              className="clickable"
              onClick={() => pickCatalogRow(row)}
              title="Use this tag in the binding form"
            >
              <td className="mono">{row.tag_id}</td>
              <td className="mono">{row.device_id}</td>
              <td>{row.datatype ?? "—"}</td>
              <td className="mono">{row.path ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3 style={{ marginTop: "1.25rem" }}>Bindings</h3>
      <table className="data">
        <thead>
          <tr>
            <th>logical_name</th>
            <th>tag_id</th>
            <th>device_id</th>
            <th>role</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {bindings.length === 0 && (
            <tr>
              <td colSpan={5}>No bindings yet.</td>
            </tr>
          )}
          {bindings.map((b) => (
            <tr key={b.logical_name}>
              <td className="mono">{b.logical_name}</td>
              <td className="mono">{b.tag_id}</td>
              <td className="mono">{b.device_id ?? "—"}</td>
              <td>{b.role ?? "input"}</td>
              <td>
                <button
                  type="button"
                  className="secondary"
                  disabled={busy}
                  onClick={() => void removeBinding(b.logical_name)}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <form className="form-grid" onSubmit={(e) => void saveBinding(e)}>
        <h3 style={{ margin: "0.5rem 0 0" }}>Add / update binding</h3>
        <label>
          Logical name
          <input
            value={logicalName}
            onChange={(e) => setLogicalName(e.target.value)}
            required
            placeholder="e.g. cell_current"
          />
        </label>
        <label>
          tag_id
          <input
            value={tagId}
            onChange={(e) => setTagId(e.target.value)}
            required
            list="catalog-tag-ids"
            placeholder="Select from catalog or type"
          />
          <datalist id="catalog-tag-ids">
            {catalog.map((row) => (
              <option
                key={`${row.device_id}:${row.tag_id}`}
                value={row.tag_id}
              />
            ))}
          </datalist>
        </label>
        <label>
          device_id
          <input
            value={deviceId}
            onChange={(e) => setDeviceId(e.target.value)}
            placeholder="optional"
          />
        </label>
        <label>
          Role
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as "input" | "output")}
          >
            <option value="input">input</option>
            <option value="output">output</option>
          </select>
        </label>
        <div className="toolbar">
          <button type="submit" className="primary" disabled={busy}>
            Save binding
          </button>
        </div>
      </form>
    </section>
  );
}
