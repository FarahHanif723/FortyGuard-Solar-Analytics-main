"""
Turns a US address (typed by the user) into lat/lon, using the US
Census Bureau's free public geocoder -- no API key required, no signup.
Good fit here since FortyGuard's coverage is U.S.-only anyway.

If the user instead types raw coordinates ("33.4484, -112.0740"), we
skip geocoding entirely and parse them directly.
"""
import re
import requests

CENSUS_GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"

COORD_PATTERN = re.compile(r"^\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*$")


def resolve_location(user_input: str) -> dict:
    """
    Returns {"lat": float, "lon": float, "resolved_name": str}
    Raises ValueError if the input can't be resolved.
    """
    coord_match = COORD_PATTERN.match(user_input)
    if coord_match:
        lat, lon = float(coord_match.group(1)), float(coord_match.group(2))
        return {"lat": lat, "lon": lon, "resolved_name": user_input.strip()}

    params = {"address": user_input, "benchmark": "Public_AR_Current", "format": "json"}
    resp = requests.get(CENSUS_GEOCODER_URL, params=params, timeout=10)
    resp.raise_for_status()
    matches = resp.json().get("result", {}).get("addressMatches", [])

    if not matches:
        raise ValueError(
            f"Couldn't find a U.S. location for '{user_input}'. "
            f"Try a more specific address, or enter coordinates as 'lat, lon'."
        )

    best = matches[0]
    coords = best["coordinates"]
    return {
        "lat": coords["y"],
        "lon": coords["x"],
        "resolved_name": best.get("matchedAddress", user_input),
    }


if __name__ == "__main__":
    print(resolve_location("1600 Pennsylvania Ave NW, Washington, DC"))
    print(resolve_location("33.4484, -112.0740"))