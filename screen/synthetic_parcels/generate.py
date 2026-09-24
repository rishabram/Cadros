#!/usr/bin/env python3
"""Generate the synthetic parcel set for the mass screener.

Deterministic: all coordinates and configs are fixed literals — no
randomness, so regenerating produces byte-identical fixtures.

Writes into this directory (screen/synthetic_parcels/):
  <parcel_id>.geojson      parcel footprint, planar feet
  <parcel_id>.zoning.json  district-appropriate zoning config (SYNTHETIC)
  <parcel_id>.finance.json synthetic pro-forma assumptions
  <parcel_id>.program.json optional building program (MU-11 parcels only)

and ../manifests/synthetic_manifest.json, which references them by path.

11 parcels exercising M-1, OS, PL, MU-11:
  syn-m1-001   M-1  rectangle 900x700
  syn-m1-002   M-1  L-shaped (large)
  syn-m1-003   M-1  large acreage 1600x1300
  syn-os-001   OS   huge rectangle 1200x4800 (~132 ac)
  syn-os-002   OS   irregular polygon (~140 ac)
  syn-pl-001   PL   rectangle 900x3200 (~66 ac)
  syn-pl-002   PL   narrow-frontage 500x3200 (~37 ac)
  syn-mu11-001 MU-11 rectangle 420x320, district-only program -> UNKNOWNs
  syn-mu11-002 MU-11 L-shaped, district-only program -> UNKNOWNs
  syn-mu11-003 MU-11 rectangle 500x400, full synthetic program -> PASS verdicts
  syn-tiny-001 MU-11 60x40 (2400 sqft < 5000 minimum) -> no schemes

NOTE on sizing: the geometry generator tiles lots as strips of width
lot_module_ft (min_frontage or 1.25x) on each side of a road, and each lot
must meet min_lot_area_sqft. So a parcel needs depth >= ~2 * min_area /
lot_module along one axis (with 2% slack). OS/PL minimums are large, hence
the big footprints above — that is realistic for those districts.

ALL outputs are labeled SYNTHETIC. Not real parcels, not real zoning.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFESTS_DIR = os.path.join(os.path.dirname(HERE), "manifests")

SYN = "SYNTHETIC fixture for screener testing. NOT a real parcel, NOT real zoning."

ZONING = {
    "M-1": {
        "min_frontage_ft": 100,
        "min_lot_area_sqft": 20000,
        "road_width_ft": 60,
        "district": "M-1",
        "zone_label": "M-1 Light Manufacturing (SYNTHETIC)",
        "source": SYN + " Illustrative industrial minimums.",
    },
    "OS": {
        "min_frontage_ft": 200,
        "min_lot_area_sqft": 435600,
        "road_width_ft": 55,
        "district": "OS",
        "zone_label": "OS Open Space (SYNTHETIC)",
        "source": SYN + " Illustrative 10-acre open-space minimums.",
    },
    "PL": {
        "min_frontage_ft": 150,
        "min_lot_area_sqft": 217800,
        "road_width_ft": 55,
        "district": "PL",
        "zone_label": "PL Public Lands (SYNTHETIC)",
        "source": SYN + " Illustrative 5-acre public-lands minimums.",
    },
    "MU-11": {
        "min_frontage_ft": 50,
        "min_lot_area_sqft": 5000,
        "road_width_ft": 55,
        "district": "MU-11",
        "zone_label": "MU-11 Mixed Use (SYNTHETIC)",
        "source": SYN + " Illustrative mixed-use minimums.",
    },
}

FINANCE = {
    "M-1": {"sale_price_per_lot": 180000, "road_cost_per_lf": 650,
            "soft_costs_fixed": 200000, "contingency_pct": 0.12,
            "source": SYN + " Placeholder industrial pro forma."},
    "OS": {"sale_price_per_lot": 250000, "road_cost_per_lf": 500,
           "soft_costs_fixed": 150000, "contingency_pct": 0.15,
           "source": SYN + " Placeholder open-space pro forma."},
    "PL": {"sale_price_per_lot": 200000, "road_cost_per_lf": 500,
           "soft_costs_fixed": 150000, "contingency_pct": 0.12,
           "source": SYN + " Placeholder public-lands pro forma."},
    "MU-11": {"sale_price_per_lot": 95000, "road_cost_per_lf": 500,
              "soft_costs_fixed": 120000, "contingency_pct": 0.10,
              "source": SYN + " Placeholder mixed-use pro forma."},
}

# Full synthetic MU-11 building program (modeled on the demo program's
# shape, values illustrative). Supplies every RuleGraph context attribute so
# this parcel's schemes evaluate to real PASS verdicts.
FULL_MU11_PROGRAM = {
    "_note": SYN + " Hypothetical building program, values illustrative.",
    "district": "MU-11",
    "building_form": "row_house",
    "stories": [{"level": 0, "use": "live_work"},
                {"level": 1, "use": "residential"},
                {"level": 2, "use": "residential"}],
    "height_ft": 38,
    "design_review_completed": True,
    "in_height_bonus_area": False,
    "open_space_ground_pct": 15,
    "enhanced_active_use_100_pct": False,
    "midblock_walkway_ft": 0,
    "front_setback_ft": 12,
    "front_street": "400 South",
    "front_street_within_listed_segment": False,
    "corner_side_setback_ft": 6,
    "corner_street": "500 East",
    "corner_street_within_listed_segment": False,
    "interior_side_setback_ft": 4,
    "interior_abuts_listed_zone": False,
    "abuts_zones_side": [],
    "rear_setback_ft": 8,
    "rear_abuts_listed_zone": False,
    "abuts_zones_rear": [],
    "is_corner_lot": True,
    "lot_abuts_sf_tf_residential": False,
    "landscape_buffer_provided": True,
}

PARCELS = [
    # (parcel_id, district, boundary coords, program or None)
    ("syn-m1-001", "M-1",
     [[0, 0], [900, 0], [900, 700], [0, 700], [0, 0]], None),
    ("syn-m1-002", "M-1",
     [[0, 0], [700, 0], [700, 400], [1100, 400], [1100, 900],
      [0, 900], [0, 0]], None),
    ("syn-m1-003", "M-1",
     [[0, 0], [1600, 0], [1600, 1300], [0, 1300], [0, 0]], None),
    ("syn-os-001", "OS",
     [[0, 0], [1200, 0], [1200, 4800], [0, 4800], [0, 0]], None),
    ("syn-os-002", "OS",
     [[0, 0], [1300, 200], [1400, 2500], [1100, 4800], [300, 5000],
      [0, 3200], [0, 0]], None),
    ("syn-pl-001", "PL",
     [[0, 0], [900, 0], [900, 3200], [0, 3200], [0, 0]], None),
    ("syn-pl-002", "PL",
     [[0, 0], [500, 0], [500, 3200], [0, 3200], [0, 0]], None),
    ("syn-mu11-001", "MU-11",
     [[0, 0], [420, 0], [420, 320], [0, 320], [0, 0]],
     {"_note": SYN, "district": "MU-11"}),
    ("syn-mu11-002", "MU-11",
     [[0, 0], [350, 0], [350, 180], [600, 180], [600, 420],
      [0, 420], [0, 0]],
     {"_note": SYN, "district": "MU-11"}),
    ("syn-mu11-003", "MU-11",
     [[0, 0], [500, 0], [500, 400], [0, 400], [0, 0]],
     FULL_MU11_PROGRAM),
    ("syn-tiny-001", "MU-11",
     [[0, 0], [60, 0], [60, 40], [0, 40], [0, 0]], None),
]


def _write(path: str, obj) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def generate() -> str:
    os.makedirs(HERE, exist_ok=True)
    os.makedirs(MANIFESTS_DIR, exist_ok=True)
    entries = []
    for parcel_id, district, boundary, program in PARCELS:
        geojson = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [boundary]},
            "properties": {
                "parcel_id": parcel_id,
                "crs": "local-feet",
                "source": SYN,
            },
        }
        zoning = dict(ZONING[district])
        finance = dict(FINANCE[district])
        _write(os.path.join(HERE, f"{parcel_id}.geojson"), geojson)
        _write(os.path.join(HERE, f"{parcel_id}.zoning.json"), zoning)
        _write(os.path.join(HERE, f"{parcel_id}.finance.json"), finance)

        entry = {
            "parcel_id": parcel_id,
            "parcel_geojson": f"../synthetic_parcels/{parcel_id}.geojson",
            "zoning_config": f"../synthetic_parcels/{parcel_id}.zoning.json",
            "finance_config": f"../synthetic_parcels/{parcel_id}.finance.json",
        }
        if program is not None:
            _write(os.path.join(HERE, f"{parcel_id}.program.json"), program)
            entry["program"] = f"../synthetic_parcels/{parcel_id}.program.json"
        entries.append(entry)

    manifest = {
        "screen_name": "synthetic-v1",
        "max_schemes": 8,
        "_note": SYN,
        "parcels": entries,
    }
    manifest_path = os.path.join(MANIFESTS_DIR, "synthetic_manifest.json")
    _write(manifest_path, manifest)
    print(f"wrote {len(entries)} parcels + manifest -> {manifest_path}")
    return manifest_path


if __name__ == "__main__":
    generate()
