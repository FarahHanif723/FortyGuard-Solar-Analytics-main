"""
Multi-site solar suitability ranker.

Accepts a list of sites -- either your own hand-picked candidates or
ones a user typed in (lat/lon, or an address you've geocoded before
calling this). Pulls temperature + solar irradiance for each via
temperature_client.get_solar_site_data(), runs each through
solar_calculator.calculate_solar_output(), and ranks them.

Sites are evaluated CONCURRENTLY (not one after another) -- each site
involves two sequential, slow API calls (heatmap + env_params, each
with its own submit-then-poll cycle that can take 10-30+ seconds), so
evaluating N sites one-by-one could take minutes and risk timing out
behind a hosting platform's request timeout. Running them in parallel
threads keeps total wall-clock time close to the single slowest site,
not the sum of all of them.

Ranking metric: highest actual_output_kw (net usable power after
heat loss) wins.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed

from temperature_client import get_solar_site_data
from solar_calculator import calculate_solar_output

DEFAULT_PANEL_CAPACITY_KW = 6.0
DEFAULT_ELECTRICITY_RATE = 0.15  # $/kWh, used when the caller doesn't provide one


def evaluate_site(site: dict) -> dict:
    """
    site: {"name": str, "lat": float, "lon": float,
           "panel_capacity_kw": float (optional), "electricity_rate_per_kwh": float (optional)}
    Returns the site dict merged with its temperature/irradiance/output data.
    """
    panel_capacity_kw = site.get("panel_capacity_kw", DEFAULT_PANEL_CAPACITY_KW)
    electricity_rate_per_kwh = site.get("electricity_rate_per_kwh", DEFAULT_ELECTRICITY_RATE)

    climate_data = get_solar_site_data(site["lat"], site["lon"])
    output_data = calculate_solar_output(
        ambient_temp_c=climate_data["temperature_c"],
        ghi=climate_data["ghi"],
        panel_capacity_kw=panel_capacity_kw,
        electricity_rate_per_kwh=electricity_rate_per_kwh,
    )
    return {
        **site,
        "panel_capacity_kw": panel_capacity_kw,
        "electricity_rate_per_kwh": electricity_rate_per_kwh,
        **climate_data,
        **output_data,
    }


def rank_sites(sites: list[dict], max_workers: int = 5) -> list[dict]:
    """
    Evaluates every site CONCURRENTLY (up to max_workers at once) and
    returns them sorted best-to-worst by actual_output_kw (highest
    first). Adds a "rank" field (1 = best).

    If one site's evaluation fails (e.g. bad coordinates, API error),
    it's skipped with a printed warning rather than failing the whole
    batch -- so one bad site doesn't take down the others.
    """
    if not sites:
        raise ValueError("No sites provided.")

    evaluated = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_site = {executor.submit(evaluate_site, site): site for site in sites}
        for future in as_completed(future_to_site):
            site = future_to_site[future]
            try:
                evaluated.append(future.result())
            except Exception as e:
                print(f"WARNING: skipping site '{site.get('name')}' -- evaluation failed: {e}")

    if not evaluated:
        raise RuntimeError("All sites failed to evaluate -- see warnings above.")

    evaluated.sort(key=lambda s: s["actual_output_kw"], reverse=True)
    for i, site in enumerate(evaluated, start=1):
        site["rank"] = i
    return evaluated


# A few default candidate sites -- shown in the demo alongside whatever
# the user types in, so the UI never looks empty on first load.
DEFAULT_SITES = [
    {"name": "Phoenix, AZ", "lat": 33.4484, "lon": -112.0740},
    {"name": "San Diego, CA", "lat": 32.7157, "lon": -117.1611},
    {"name": "Austin, TX", "lat": 30.2672, "lon": -97.7431},
]


if __name__ == "__main__":
    ranked = rank_sites(DEFAULT_SITES)
    for site in ranked:
        print(f"#{site['rank']} {site['name']}: "
              f"{site['actual_output_kw']} kW actual output "
              f"({site['efficiency_loss_percent']}% heat loss, "
              f"risk: {site['risk_level']})")