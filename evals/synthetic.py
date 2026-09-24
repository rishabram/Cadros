"""Synthetic exact-geometry case generation (build plan §9 Phase D, §14).

Uses our own deterministic geometry engine to procedurally generate test
cases with known-valid ground truth. Seeded -> identical output every run.

NOTE (founder directive): synthetic data is for TESTING the engine and the
eval harness only — never for training the model. Training uses real,
rights-cleared maps.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
from typing import Dict, List

from shapely.geometry import Polygon

from prototype import geometry

ZONING_PRESETS = [
    {"zone_label": "R-1-8 (synthetic)", "min_lot_area_sqft": 8000,
     "min_frontage_ft": 70, "road_width_ft": 55,
     "source": "synthetic preset"},
    {"zone_label": "R-1-6 (synthetic)", "min_lot_area_sqft": 6000,
     "min_frontage_ft": 60, "road_width_ft": 50,
     "source": "synthetic preset"},
]

FINANCE_PRESET = {
    "sale_price_per_lot": 95000,
    "road_cost_per_lf": 500,
    "soft_costs_fixed": 120000,
    "contingency_pct": 0.10,
    "source": "synthetic preset",
}


def random_parcel(rng: random.Random, target_acres: float) -> List[List[float]]:
    """Irregular n-gon (5-8 vertices) scaled to a target acreage."""
    n = rng.randint(5, 8)
    angles = sorted(rng.uniform(0, 2 * math.pi) for _ in range(n))
    radii = [rng.uniform(0.75, 1.15) for _ in range(n)]
    pts = [(r * math.cos(a), r * math.sin(a)) for r, a in zip(radii, angles)]
    poly = Polygon(pts).buffer(0)
    target_sqft = target_acres * 43560
    scale = math.sqrt(target_sqft / poly.area)
    return [[round(x * scale, 2), round(y * scale, 2)] for x, y in poly.exterior.coords]


def generate_cases(n: int, seed: int, out_dir: str) -> List[str]:
    """Generate n cases; returns list of written paths. Fully deterministic."""
    os.makedirs(out_dir, exist_ok=True)
    rng = random.Random(seed)
    paths = []
    for i in range(n):
        acres = rng.uniform(3.0, 6.0)
        boundary = random_parcel(rng, acres)
        zoning = dict(rng.choice(ZONING_PRESETS))
        parcel_id = f"synth-{seed}-{i:03d}"
        schemes = geometry.generate_schemes(boundary, zoning, parcel_id, max_schemes=6)
        if not schemes:
            continue  # degenerate draw; skip (still deterministic)
        top = max(schemes, key=lambda s: len(s.lots))
        case = {
            "meta": {"case_id": parcel_id, "seed": seed,
                     "note": "synthetic engine-test case; NOT training data"},
            "parcel": {"parcel_id": parcel_id, "boundary": boundary,
                       "crs": "local-feet", "source": "synthetic generator"},
            "zoning": zoning,
            "finance": FINANCE_PRESET,
            "ground_truth": {
                "scheme_id": top.scheme_id,
                "lot_count": len(top.lots),
                "lots": [lot.polygon for lot in top.lots],
                "params": top.params,
                "fingerprint": top.fingerprint,
            },
        }
        path = os.path.join(out_dir, f"{parcel_id}.json")
        with open(path, "w") as f:
            json.dump(case, f, indent=1)
        paths.append(path)
    return paths


def cases_fingerprint(paths: List[str]) -> str:
    h = hashlib.sha256()
    for p in sorted(paths):
        with open(p, "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:16]


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="inputs/synthetic")
    args = ap.parse_args()
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = args.out if os.path.isabs(args.out) else os.path.join(base, args.out)
    paths = generate_cases(args.n, args.seed, out)
    print(f"wrote {len(paths)} synthetic cases to {out} "
          f"(fingerprint {cases_fingerprint(paths)})")
