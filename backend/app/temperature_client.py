"""
SolarShield -- Temperature + Solar Irradiance client.

Uses the OFFICIAL FortyGuard `fortyguard` package (from the cloned
temperature-api-quickstart repo). Copy the `fortyguard/` folder from
that repo into this project's root so `from fortyguard import
FortyGuardClient` works.

Pipeline (matches FortyGuard's own recommended pattern):
  1. create_heatmap()             -> ambient/peak temperature (°C) for the point
  2. environmental_parameters()   -> uses that temperature as the anchor,
                                      returns solar irradiance (GHI/DNI/DHI)
                                      + heat index + humidity etc.
"""
import sys
import pathlib
import time

# Make the project root (parent of this app/ folder) importable, so
# `fortyguard/` (which sits as a sibling of app/) can be found -- this
# works whether the script is run directly or imported by another file.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
# Load the .env file from the project root (parent of app/), regardless
# of which directory the script is run from.
load_dotenv(pathlib.Path(__file__).resolve().parent.parent / ".env")

from fortyguard import FortyGuardClient

client = FortyGuardClient()  # now reads FORTYGUARD_API_KEY from the loaded .env

USE_MOCK = False  # flip to True to skip live API calls during dev/demo


def _small_polygon(lat: float, lon: float, delta: float = 0.003) -> dict:
    """~650m box around the point -- safely bigger than one 60m tile.
    Must be a FeatureCollection wrapping the Polygon (matches the
    official quickstart's create_heatmap example exactly) -- a bare
    Polygon is silently accepted by the API but returns zero cells."""
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [lon - delta, lat - delta],
                    [lon + delta, lat - delta],
                    [lon + delta, lat + delta],
                    [lon - delta, lat + delta],
                    [lon - delta, lat - delta],
                ]],
            },
        }],
    }


def _extract_avg_temp_celsius(result: dict) -> float:
    """
    Official docs schema uses capitalized keys: stats_data.Temperature_stats.Mean
    Try that first, then lowercase variants, then a per-tile fallback,
    to cover any casing differences between doc examples and live responses.
    """
    stats = result.get("stats_data", {})

    for stats_key in ("Temperature_stats", "temperature_stats"):
        temp_stats = stats.get(stats_key)
        if temp_stats:
            for mean_key in ("Mean", "mean"):
                if mean_key in temp_stats:
                    return float(temp_stats[mean_key])

    features = result.get("map_data", {}).get("features", [])
    for prop_key in ("average_temperature", "Average_temperature", "temperature", "value"):
        temps = [f["properties"][prop_key] for f in features
                 if prop_key in f.get("properties", {})]
        if temps:
            return sum(temps) / len(temps)

    raise ValueError(f"Could not find temperature in response: {result}")


def get_solar_site_data(lat: float, lon: float, date: str = None, time_str: str = "14:00") -> dict:
    """
    The only function the rest of the app should call.

    Returns:
      {
        "temperature_c": float, "temperature_f": float,
        "ghi": float, "dni": float, "dhi": float,   # W/m^2
        "heat_index_c": float, "humidity_percent": float,
        "source": "live" | "mock"
      }
    """
    if USE_MOCK:
        return {
            "temperature_c": 42.5, "temperature_f": 108.5,
            "ghi": 850.0, "dni": 720.0, "dhi": 130.0,
            "heat_index_c": 47.0, "humidity_percent": 18.0,
            "source": "mock"
        }

    if date is None:
        # Use a few days back, not today -- very recent dates can have a
        # short processing delay and return zero cells even though
        # they're technically within the supported range.
        import datetime
        date = (datetime.date.today() - datetime.timedelta(days=5)).strftime("%Y-%m-%d")

    # Step 1: ambient temperature from the heatmap
    heatmap_resp = client.create_heatmap(
        polygon_aoi=_small_polygon(lat, lon),
        start_date=date,
        start_time=time_str,
        filter_type=1,
        granularity=60,
    )
    result = heatmap_resp["result"]
    temp_c = _extract_avg_temp_celsius(result)

    # Step 2: solar irradiance + comfort params, anchored to that temperature
    env_resp = client.environmental_parameters(
        latitude=lat,
        longitude=lon,
        temperature=temp_c,
        start_date=date,
        start_time=time_str,
        filter_type=1,
    )
    location = env_resp["result"]["locations"][0]
    solar = location.get("solar_irradiance", {}).get("clear_sky", {})
    params = location.get("parameters", {})

    return {
        "temperature_c": round(temp_c, 1),
        "temperature_f": round(temp_c * 9 / 5 + 32, 1),
        "ghi": solar.get("ghi"),
        "dni": solar.get("dni"),
        "dhi": solar.get("dhi"),
        "heat_index_c": params.get("heat_index_celsius"),
        "humidity_percent": params.get("relative_humidity_percent"),
        "source": "live",
    }


if __name__ == "__main__":
    print(get_solar_site_data(33.4484, -112.0740))  # Phoenix, AZ