import logo from "../assets/fortyguard_logo.png";

export default function Navbar({ backendOk }) {
  return (
    <header className="nav">
      <div className="brand">
        <img src={logo} alt="FortyGuard" className="brand-logo" />
        <div>
          <div className="brand-name">SolarShield</div>
          <div className="brand-tag">Smart Solar Site Intelligence</div>
        </div>
      </div>
      <div className="nav-right">
        <div className="status-pill">
          <span className={`status-dot ${backendOk ? "" : "off"}`}></span>
          {backendOk ? "FortyGuard API connected" : "Backend not reachable"}
        </div>
      </div>
    </header>
  );
}

