const RISK_LABEL = { low: "Low", moderate: "Moderate", high: "High", extreme: "Extreme" };

export default function SiteCard({ site }) {
  const risk = (site.risk_level || "low").toLowerCase();

  return (
    <div className={`site-card ${site.rank === 1 ? "rank-1" : ""}`}>
      <div className="rank-badge">#{site.rank}</div>

      <div className="site-main">
        <div className="site-name-row">
          <span className="site-name">{site.name}</span>
        </div>
        <div className="site-addr">{site.resolved_location || `${site.lat}, ${site.lon}`}</div>

        <div className="stat-grid">
          <div className="stat">
            <span className="val">{site.temperature_f}°F</span>
            <span className="lbl">Temp</span>
          </div>
          <div className="stat">
            <span className="val">{site.ghi_w_m2 ?? "—"} W/m²</span>
            <span className="lbl">Irradiance</span>
          </div>
          <div className="stat">
            <span className="val">{site.actual_output_kw} kW</span>
            <span className="lbl">Actual Output</span>
          </div>
          <div className="stat loss">
            <span className="val">{site.efficiency_loss_percent}%</span>
            <span className="lbl">Efficiency Loss</span>
          </div>
          <div className="stat dollar">
            <span className="val">${site.dollar_lost_per_year}</span>
            <span className="lbl">Lost / Year</span>
          </div>
        </div>
      </div>

      <div className={`risk-badge risk-${risk}`}>
        <span className="risk-dot"></span>
        {RISK_LABEL[risk] || risk}
      </div>
    </div>
  );
}
