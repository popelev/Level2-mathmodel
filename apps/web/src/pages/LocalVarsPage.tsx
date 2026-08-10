import { useEffect, useState } from "react";
import { api } from "../api";
import type { LocalVar } from "../types";

function valueToInput(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

function parseValue(raw: string): unknown {
  const trimmed = raw.trim();
  if (trimmed === "") return null;
  try {
    return JSON.parse(trimmed) as unknown;
  } catch {
    return trimmed;
  }
}

export function LocalVarsPage() {
  const [vars, setVars] = useState<LocalVar[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [name, setName] = useState("");
  const [value, setValue] = useState("");
  const [unit, setUnit] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function load() {
    setError("");
    try {
      const list = await api.listLocalVars();
      setVars(list);
      if (!selectedId && list[0]) {
        selectVar(list[0]);
      } else if (selectedId) {
        const current = list.find((v) => v.id === selectedId);
        if (current) selectVar(current);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  function selectVar(v: LocalVar) {
    setSelectedId(v.id);
    setName(v.name);
    setValue(valueToInput(v.value));
    setUnit(v.unit ?? "");
    setDescription(v.description ?? "");
  }

  async function save() {
    if (!selectedId) return;
    setSaving(true);
    setError("");
    try {
      await api.updateLocalVar(selectedId, {
        id: selectedId,
        name,
        value: parseValue(value),
        unit: unit || undefined,
        description: description || undefined,
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <section className="panel">
      <h2>Local variables</h2>
      <p className="lead">
        Engine-owned variables only (mock). No writes to Level2/PLC.
      </p>

      <div className="toolbar">
        <button type="button" className="secondary" onClick={() => void load()}>
          Refresh list
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      <table className="data">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Value</th>
            <th>Unit</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {vars.map((v) => (
            <tr key={v.id}>
              <td className="mono">{v.id}</td>
              <td>{v.name}</td>
              <td className="mono">{valueToInput(v.value)}</td>
              <td>{v.unit || "—"}</td>
              <td>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => selectVar(v)}
                >
                  Edit
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {selectedId && (
        <div className="form-grid">
          <h3 style={{ margin: "0.5rem 0 0" }}>Editing: {selectedId}</h3>
          <label>
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <label>
            Value (JSON or string)
            <input value={value} onChange={(e) => setValue(e.target.value)} />
          </label>
          <label>
            Unit
            <input value={unit} onChange={(e) => setUnit(e.target.value)} />
          </label>
          <label>
            Description
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </label>
          <div className="toolbar">
            <button
              type="button"
              className="primary"
              disabled={saving}
              onClick={() => void save()}
            >
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
