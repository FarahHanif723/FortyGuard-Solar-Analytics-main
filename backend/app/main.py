"""
SolarShield FastAPI app.

POST /rank-sites
  Body: {
    "sites": [
      {"name": "My Rooftop", "location": "1600 Pennsylvania Ave NW, Washington, DC",
       "panel_capacity_kw": 6.0, "electricity_rate_per_kwh": 0.15},
      ...
    ],
    "include_defaults": true   # also evaluate the 3 built-in demo sites
  }
  Returns: ranked sites + AI recommendation, ready for the frontend to render.

GET /health
  Simple liveness check.
"""
import sys
import pathlib

# Make this app/ folder importable as a flat directory (not just as the
# "app" package) so sibling modules like geocode_helper.py resolve the
# same way whether this file is run directly, imported by a script, or
# loaded by uvicorn as "app.main" from the project root.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

from geocode_helper import resolve_location
from site_ranker import rank_sites, DEFAULT_SITES
from recommendation_agent import generate_recommendation

app = FastAPI(title="SolarShield API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your frontend's actual domain before final submission
    allow_methods=["*"],
    allow_headers=["*"],
)


class SiteInput(BaseModel):
    name: str
    location: str = Field(..., description="A U.S. address, or 'lat, lon' coordinates")
    panel_capacity_kw: Optional[float] = None
    electricity_rate_per_kwh: Optional[float] = None


class RankSitesRequest(BaseModel):
    sites: list[SiteInput] = []
    include_defaults: bool = True


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/rank-sites")
def rank_sites_endpoint(request: RankSitesRequest):
    if not request.sites and not request.include_defaults:
        raise HTTPException(status_code=400, detail="Provide at least one site, or set include_defaults=true.")

    resolved_sites = []

    for site_input in request.sites:
        try:
            location = resolve_location(site_input.location)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        site = {
            "name": site_input.name,
            "lat": location["lat"],
            "lon": location["lon"],
            "resolved_location": location["resolved_name"],
        }
        if site_input.panel_capacity_kw is not None:
            site["panel_capacity_kw"] = site_input.panel_capacity_kw
        if site_input.electricity_rate_per_kwh is not None:
            site["electricity_rate_per_kwh"] = site_input.electricity_rate_per_kwh

        resolved_sites.append(site)

    if request.include_defaults:
        resolved_sites.extend(DEFAULT_SITES)

    try:
        ranked = rank_sites(resolved_sites)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FortyGuard API error: {e}")

    try:
        recommendation = generate_recommendation(ranked)
    except Exception as e:
        recommendation = {"error": f"AI recommendation failed: {e}"}

    return {
        "ranked_sites": ranked,
        "recommendation": recommendation,
    }