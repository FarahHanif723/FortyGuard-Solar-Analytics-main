import { useState } from "react";

const emptyRow = () => ({ name: "", location: "", capacity: "", rate: "" });

export default function SiteForm({ onSubmit, loading }) {
  const [rows, setRows] = useState([emptyRow()]);
  const [includeDefaults, setIncludeDefaults] = useState(true);

  const updateRow = (index, field, value) => {
    setRows((prev) => prev.map((r, i) => (i === index ? { ...r, [field]: value } : r)));
  };

  const addRow = () => setRows((prev) => [...prev, emptyRow()]);

  const removeRow = (index) => {
    setRows((prev) => (prev.length > 1 ? prev.filter((_, i) => i !== index) : prev));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const sites = rows
      .filter((r) => r.name.trim() && r.location.trim())
      .map((r) => ({
        name: r.name.trim(),
        location: r.location.trim(),
        ...(r.capacity ? { panel_capacity_kw: parseFloat(r.capacity) } : {}),
        ...(r.rate ? { electricity_rate_per_kwh: parseFloat(r.rate) } : {}),
      }));
    onSubmit({ sites, include_defaults: includeDefaults });
  };

  return (
    <section className="form-card">
      <h2>Add sites to analyze</h2>
      <p className="hint">
        Use a U.S. address or "lat, lon" coordinates. Capacity and rate are optional — defaults apply if left blank.
      </p>

      <form onSubmit={handleSubmit}>
        <div>
          {rows.map((row, i) => (
            <div className="site-row" key={i}>
              <div className="field">
                <label>Site name</label>
                <input
                  type="text"
                  placeholder="e.g. Rooftop A"
                  value={row.name}
                  onChange={(e) => updateRow(i, "name", e.target.value)}
                  required
                />
              </div>
              <div className="field">
                <label>Location</label>
                <input
                  type="text"
                  placeholder="Address or lat, lon"
                  value={row.location}
                  onChange={(e) => updateRow(i, "location", e.target.value)}
                  required
                />
              </div>
              <div className="field">
                <label>Panel capacity (kW)</label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="6.0"
                  value={row.capacity}
                  onChange={(e) => updateRow(i, "capacity", e.target.value)}
                />
              </div>
              <div className="field">
                <label>Rate ($/kWh)</label>
                <input
                  type="number"
                  step="0.01"
                  placeholder="0.15"
                  value={row.rate}
                  onChange={(e) => updateRow(i, "rate", e.target.value)}
                />
              </div>
              <button
                type="button"
                className="row-remove"
                onClick={() => removeRow(i)}
                disabled={rows.length === 1}
                title="Remove site"
              >
                ✕
              </button>
            </div>
          ))}
        </div>

        <div className="form-actions">
          <div style={{ display: "flex", alignItems: "center", gap: 18, flexWrap: "wrap" }}>
            <button type="button" className="btn-ghost" onClick={addRow}>
              + Add another site
            </button>
            <label className="toggle-row">
              <input
                type="checkbox"
                checked={includeDefaults}
                onChange={(e) => setIncludeDefaults(e.target.checked)}
              />
              Include demo sites (Phoenix, San Diego, Austin)
            </label>
          </div>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Analyzing…" : "Analyze Sites →"}
          </button>
        </div>
      </form>
    </section>
  );
}
