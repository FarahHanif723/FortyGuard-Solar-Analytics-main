"""
One-shot diagnostic: tries 4 variations of the create_heatmap call to
isolate exactly which factor is causing n_cells=0.
Run: python app/diagnose_heatmap.py
"""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(pathlib.Path(__file__).resolve().parent.parent / ".env")

from fortyguard import FortyGuardClient

client = FortyGuardClient()


def nyc_polygon(delta=0.007):
    """Exact style from the official README example (NYC area)."""
    lat, lon = 40.7115, -74.010
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature", "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [lon - delta, lat - delta], [lon + delta, lat - delta],
                    [lon + delta, lat + delta], [lon - delta, lat + delta],
                    [lon - delta, lat - delta],
                ]],
            },
        }],
    }


def phoenix_polygon(delta=0.003):
    lat, lon = 33.4484, -112.0740
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature", "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [lon - delta, lat - delta], [lon + delta, lat - delta],
                    [lon + delta, lat + delta], [lon - delta, lat + delta],
                    [lon - delta, lat - delta],
                ]],
            },
        }],
    }


def run_test(label, polygon_aoi, start_date, start_time, granularity):
    print(f"\n--- {label} ---")
    print(f"date={start_date} time={start_time} granularity={granularity}")
    try:
        resp = client.create_heatmap(
            polygon_aoi=polygon_aoi,
            start_date=start_date,
            start_time=start_time,
            filter_type=1,
            granularity=granularity,
        )
        n_cells = resp["result"].get("stats_data", {}).get("n_cells", "?")
        print(f"RESULT: n_cells={n_cells}")
        if n_cells and n_cells != 0 and n_cells != "?":
            print("SUCCESS -- this combination works!")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    # Test 1: README's own known-good example (NYC, known historical date, granularity=100)
    run_test("Test 1: README example (NYC, 2024-07-15, gran=100)",
              nyc_polygon(), "2024-07-15", "14:00", 100)

    # Test 2: Same but granularity=60 -- checks if 60m is the problem
    run_test("Test 2: NYC, 2024-07-15, gran=60",
              nyc_polygon(), "2024-07-15", "14:00", 60)

    # Test 3: Phoenix coords, same known-good date/granularity -- checks if location is the problem
    run_test("Test 3: Phoenix, 2024-07-15, gran=100",
              phoenix_polygon(), "2024-07-15", "14:00", 100)

    # Test 4: Phoenix coords, recent date -- checks if recency is the problem
    import datetime
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    run_test(f"Test 4: Phoenix, {yesterday} (yesterday), gran=100",
              phoenix_polygon(), yesterday, "14:00", 100)