import { useEffect, useState } from "react";
import { api } from "../api";
import type { LiveInputsSummary } from "../types";

export function LiveInputsPage() {
  const [data, setData] = useState<LiveInputsSummary | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setData(await api.liveInputs());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <section className="panel">
      <h2>Live inputs</h2>
      <p className="lead">
        Read-only projection of Level2 tags (BFF mock data, no PLC writes).
      </p>

      <div className="toolbar">
        <button type="button" className="primary" onClick={() => void load()}>
          Refresh
        </button>
        {data && (
          <span className="muted">
            source: {data.source} · updated: {data.updated_at}
          </span>
        )}
      </div>

      {loading && <p className="muted">loading…</p>}
      {error && <p className="error">{error}</p>}

      {data && (
        <table className="data">
          <thead>
            <tr>
              <th>Tag</th>
              <th>Device</th>
              <th>Value</th>
              <th>Quality</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {data.tags.map((tag) => (
              <tr key={tag.tag_id}>
                <td className="mono">{tag.tag_id}</td>
                <td className="mono">{tag.device_id ?? "—"}</td>
                <td className="mono">
                  {tag.value_num === null || tag.value_num === undefined
                    ? "null"
                    : tag.value_num}
                </td>
                <td>
                  <span className={`badge ${tag.quality === 0 ? "ok" : "bad"}`}>
                    {tag.quality === 0 ? "Good" : "Bad"}
                  </span>
                </td>
                <td className="mono">{tag.time ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
