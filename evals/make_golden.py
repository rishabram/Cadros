"""Snapshot golden fixtures: run the deterministic pipeline once per golden
input and store outputs as immutable expected values.

Golden files are regression anchors — run_evals.py replays the pipeline and
requires the outputs to match. Regenerate ONLY after deliberate review
(human verifies lot counts / geometry are sane first).
"""
from __future__ import annotations

import json
import os
import tempfile

from prototype import pipeline

GOLDENS = {
    "golden_01": {
        "meta": {
            "name": "golden_01",
            "note": "Demo parcel, 3.61 ac, R-1-8 synthetic zoning. Snapshot of "
                    "deterministic pipeline output (lot counts human-verified).",
            "max_schemes": 8,
        },
        "parcel": {
            "parcel_id": "demo-utah-001",
            "boundary": [[0, 0], [170, 12], [330, -8], [465, 45], [495, 175],
                         [440, 295], [385, 375], [210, 360], [70, 330], [-15, 185]],
            "crs": "local-feet",
            "source": "synthetic demo",
        },
        "zoning": {
            "zone_label": "R-1-8 (synthetic demo)",
            "min_lot_area_sqft": 8000,
            "min_frontage_ft": 70,
            "road_width_ft": 55,
            "source": "synthetic demo params",
        },
        "finance": {
            "sale_price_per_lot": 95000,
            "road_cost_per_lf": 500,
            "soft_costs_fixed": 120000,
            "contingency_pct": 0.10,
            "source": "demo assumptions",
        },
    },
    "golden_02": {
        "meta": {
            "name": "golden_02",
            "note": "Large near-rectangular parcel, ~5.4 ac, smaller-lot R-1-6 "
                    "zoning. Exercises higher-yield regime.",
            "max_schemes": 8,
        },
        "parcel": {
            "parcel_id": "golden-02-rect",
            "boundary": [[0, 0], [560, 20], [580, 380], [540, 430], [20, 420], [-10, 200]],
            "crs": "local-feet",
            "source": "synthetic golden",
        },
        "zoning": {
            "zone_label": "R-1-6 (synthetic)",
            "min_lot_area_sqft": 6000,
            "min_frontage_ft": 60,
            "road_width_ft": 50,
            "source": "synthetic golden params",
        },
        "finance": {
            "sale_price_per_lot": 82000,
            "road_cost_per_lf": 500,
            "soft_costs_fixed": 140000,
            "contingency_pct": 0.10,
            "source": "demo assumptions",
        },
    },
    "golden_03": {
        "meta": {
            "name": "golden_03",
            "note": "Awkward quasi-triangular parcel, ~3.4 ac, R-1-8. Hard case: "
                    "narrow corners should be filtered by frontage/area rules.",
            "max_schemes": 8,
        },
        "parcel": {
            "parcel_id": "golden-03-tri",
            "boundary": [[0, 0], [520, 20], [430, 300], [260, 420], [80, 250]],
            "crs": "local-feet",
            "source": "synthetic golden",
        },
        "zoning": {
            "zone_label": "R-1-8 (synthetic)",
            "min_lot_area_sqft": 8000,
            "min_frontage_ft": 70,
            "road_width_ft": 55,
            "source": "synthetic golden params",
        },
        "finance": {
            "sale_price_per_lot": 95000,
            "road_cost_per_lf": 500,
            "soft_costs_fixed": 120000,
            "contingency_pct": 0.10,
            "source": "demo assumptions",
        },
    },
}


def main() -> None:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gdir = os.path.join(base, "inputs", "golden")
    os.makedirs(gdir, exist_ok=True)
    for name, g in GOLDENS.items():
        tmp = tempfile.mkdtemp(prefix="golden_")
        res = pipeline.run_pipeline_objects(
            g["parcel"]["parcel_id"],
            g["parcel"]["boundary"],
            {"crs": g["parcel"]["crs"]},
            g["zoning"],
            g["finance"],
            tmp,
            max_schemes=g["meta"]["max_schemes"],
        )
        expected = {
            "scheme_count": len(res["ranked"]),
            "ranked_order": res["report"]["ranked_order"],
            "top_scheme_lots": len(res["ranked"][0].lots),
            "top_scheme_profit": res["proformas"][res["ranked"][0].scheme_id].profit,
            "all_clean": all(
                all(c.status != "fail" for c in v)
                for v in res["validations"].values()
            ),
            "schemes": [
                {
                    "scheme_id": s.scheme_id,
                    "lots": [lot.polygon for lot in s.lots],
                    "params": s.params,
                    "fingerprint": s.fingerprint,
                }
                for s in res["ranked"]
            ],
        }
        out = dict(g)
        out["expected"] = expected
        path = os.path.join(gdir, f"{name}.json")
        with open(path, "w") as f:
            json.dump(out, f, indent=1)
        tops = [(s.scheme_id, len(s.lots)) for s in res["ranked"][:3]]
        print(f"{name}: {len(res['ranked'])} schemes, top lots {tops}, "
              f"all_clean={expected['all_clean']} -> {path}")


if __name__ == "__main__":
    main()
