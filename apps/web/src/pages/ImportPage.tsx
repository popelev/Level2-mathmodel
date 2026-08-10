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
        Read-only catalog import from Level2 (`GET /tags`). Bindings map stable
        tag_id to logical names. Model outputs stay in local variables.
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
      <table className="data">
        <thead>
          <tr>
            <th>tag_id</th>
            <th>device_id</th>
            <th>datatype</th>
            <th>path</th>
            <th>enabled</th>
          </tr>
        </thead>
        <tbody>
          {catalog.length === 0 && (
            <tr>
              <td colSpan={5}>No catalog entries yet.</td>
            </tr>
          )}
          {catalog.map((row) => (
            <tr key={`${row.device_id}:${row.tag_id}`}>
              <td className="mono">{row.tag_id}</td>
              <td className="mono">{row.device_id}</td>
              <td>{row.datatype ?? "—"}</td>
              <td className="mono">{row.path ?? "—"}</td>
              <td>{row.enabled === undefined ? "—" : String(row.enabled)}</td>
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
          />
        </label>
        <label>
          tag_id
          <input
            value={tagId}
            onChange={(e) => setTagId(e.target.value)}
            required
          />
        </label>
        <label>
          device_id
          <input
            value={deviceId}
            onChange={(e) => setDeviceId(e.target.value)}
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
