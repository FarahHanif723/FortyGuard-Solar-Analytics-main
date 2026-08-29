import { useState } from "react";
import Navbar from "./components/Navbar.jsx";
import SiteForm from "./components/SiteForm.jsx";
import SiteCard from "./components/SiteCard.jsx";
import AIPanel from "./components/AIPanel.jsx";
import LoadingStatus from "./components/LoadingStatus.jsx";
import footerLogo from "./assets/fortyguard_logo_footer.png";
import coverBg from "./assets/cover_bg.png";


// e.g. "https://solarshield-backend.onrender.com"
const BACKEND_URL = "https://fortyguard-solar-analytics-main-production.up.railway.app";

export default function App() {
  const [rankedSites, setRankedSites] = useState([]);
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [backendOk, setBackendOk] = useState(true);

  const handleAnalyze = async ({ sites, include_defaults }) => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${BACKEND_URL}/rank-sites`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sites, include_defaults }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Server responded ${res.status}`);
      }

      const data = await res.json();
      setRankedSites(data.ranked_sites || []);
      setRecommendation(data.recommendation || null);
      setBackendOk(true);
    } catch (err) {
      setBackendOk(false);
      setError(
        err.message.includes("fetch")
          ? "Couldn't reach the backend. Is it running, and is BACKEND_URL set correctly in App.jsx?"
          : err.message
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar backendOk={backendOk} />

      <main>
        <div
          className="hero-row hero-with-bg"
          style={{ backgroundImage: `url(${coverBg})` }}
        >
          <div>
            <div className="hero-title">Compare sites before you install.</div>
            <div className="hero-sub">
              Enter candidate locations — SolarShield pulls live temperature and irradiance data to
              rank real usable output, not just sunlight.
            </div>
          </div>
          <div className="grain-badge">Live heat-loss modeling</div>
        </div>

        <SiteForm onSubmit={handleAnalyze} loading={loading} />

        <div className="section-label">
          <span>Ranked results</span>
          <span className="line"></span>
        </div>

        {error && <div className="error-banner">{error}</div>}

        {loading && <LoadingStatus />}

        {rankedSites.length === 0 && !loading && !error && (
          <div className="empty-state">
            No results yet — add a site above and hit "Analyze Sites" to see rankings.
          </div>
        )}

        <div className="site-cards">
          {rankedSites.map((site) => (
            <SiteCard key={site.name + site.rank} site={site} />
          ))}
        </div>

        {recommendation && (
          <>
            <div className="section-label">
              <span>AI recommendation</span>
              <span className="line"></span>
            </div>
            <AIPanel recommendation={recommendation} />
          </>
        )}
      </main>

      <footer>
        <img src={footerLogo} alt="FortyGuard" className="footer-logo" />
        <div>SolarShield — built on the FortyGuard tOS Enterprise API</div>
      </footer>
    </>
  );
}
