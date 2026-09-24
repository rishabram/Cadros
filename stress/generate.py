"""Deterministic synthetic parcel generator for the 10k stress test.

Seed 20260924, stdlib random only. Same seed -> byte-identical manifest.
Writes stress/manifest_10k.json with inline parcel_geojson / zoning_config /
finance_config dicts (the screener accepts inline values).
"""
from __future__ import annotations

import json
import math
import os
import random

SEED = 20260924
N_PARCELS = 10_000
SQFT_PER_ACRE = 43560

# District mix mirrors the real 500-parcel county screen x20.
DISTRICT_MIX = {
    "M-1": 1180, "R-1-7000": 3180, "R-1-5000": 260, "RMF-30": 20,
    "OS": 700, "M-2": 760, "EI": 60, "MU-5": 2740,
    "FR-3": 420, "FR-2": 400, "BP": 260, "MU-11": 20,
}
assert sum(DISTRICT_MIX.values()) == N_PARCELS

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRATCH = os.path.dirname(_HERE)


def _rect(w, h):
    return [[0, 0], [w, 0], [w, h], [0, h], [0, 0]]


def _lshape(w, h, rng):
    # Rectangle minus a corner notch (deterministic via rng).
    cw, ch = w * rng.uniform(0.3, 0.6), h * rng.uniform(0.3, 0.6)
    return [
        [0, 0], [w, 0], [w, h], [w - cw, h],
        [w - cw, h - ch], [0, h - ch], [0, 0],
    ]


def _trapezoid(w, h, rng):
    dx = w * rng.uniform(0.05, 0.25)
    return [[0, 0], [w, 0], [w - dx, h], [dx, h], [0, 0]]


def _rotate(pts, angle_deg):
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    return [[x * ca - y * sa, x * sa + y * ca] for x, y in pts]


def make_polygon(rng):
    acres = math.exp(rng.uniform(math.log(0.5), math.log(40.0)))
    area = acres * SQFT_PER_ACRE
    fam = rng.random()
    if fam < 0.40:
        aspect = rng.uniform(1.0, 4.0)
        w = math.sqrt(area * aspect)
        pts = _rect(w, area / w)
        family = "rect"
    elif fam < 0.70:
        aspect = rng.uniform(1.0, 3.0)
        w = math.sqrt(area * 1.25 * aspect)
        pts = _lshape(w, (area * 1.25) / w, rng)
        family = "lshape"
    elif fam < 0.90:
        aspect = rng.uniform(1.0, 3.0)
        w = math.sqrt(area * aspect)
        pts = _trapezoid(w, area / w, rng)
        family = "trapezoid"
    else:
        aspect = rng.uniform(4.0, 8.0)
        w = math.sqrt(area * aspect)
        pts = _rect(w, area / w)
        family = "skinny"
    return _rotate(pts, rng.uniform(0, 90)), family, round(acres, 2)


def main():
    with open(os.path.join(_SCRATCH, "screen", "real_manifest_v2.json")) as f:
        real = json.load(f)
    zoning_by_district, finance_by_district = {}, {}
    for e in real["parcels"]:
        z = e.get("zoning_config")
        if isinstance(z, dict) and z.get("district") not in zoning_by_district:
            zoning_by_district[z["district"]] = z
            fc = e.get("finance_config")
            finance_by_district[z["district"]] = fc if isinstance(fc, dict) else {}

    rng = random.Random(SEED)
    districts = []
    for d, n in DISTRICT_MIX.items():
        districts.extend([d] * n)
    rng.shuffle(districts)

    parcels = []
    for i, district in enumerate(districts):
        coords, family, acres = make_polygon(rng)
        pid = f"stress-{i + 1:05d}"
        parcels.append({
            "parcel_id": pid,
            "parcel_geojson": {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [coords]},
                "properties": {
                    "parcel_id": pid,
                    "synthetic": True,
                    "shape_family": family,
                    "area_acres_nominal": acres,
                    "generator": "stress/generate.py",
                    "generator_seed": SEED,
                    "source": "SYNTHETIC fixture for 10k stress test. NOT a real parcel.",
                },
            },
            "zoning_config": zoning_by_district[district],
            "finance_config": finance_by_district[district],
        })

    manifest = {
        "_note": ("10k synthetic stress manifest. Deterministic: seed 20260924. "
                  "Zoning/finance configs verbatim from real_manifest_v2.json; "
                  "only parcel polygons are synthetic."),
        "screen_name": "stress-10k-synthetic",
        "max_schemes": 8,
        "parcels": parcels,
    }
    out = os.path.join(_HERE, "manifest_10k.json")
    with open(out, "w") as f:
        json.dump(manifest, f)
    print(f"wrote {out}: {len(parcels)} parcels, "
          f"{os.path.getsize(out) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
