"""Regression tests for the 30-parcel benchmark harness (screen/benchmark.py).

MACHINE-DRAFT scope: these tests exercise pipeline-geometry evaluation
determinism only. They produce and imply no human zoning-rule verdicts.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from screen.benchmark import SAMPLE, run_benchmark


def _fixture_manifest(path: str) -> str:
    """Write a 3-parcel synthetic fixture manifest; return its path."""
    def square(w: float, h: float):
        return [[0, 0], [w, 0], [w, h], [0, h], [0, 0]]

    zoning = {
        "district": "R-1-8",
        "zone_label": "fixture (synthetic, test-only)",
        "min_lot_area_sqft": 8000,
        "min_frontage_ft": 70,
        "road_width_ft": 55,
        "source": "test fixture",
    }
    finance = {
        "road_cost_per_lf": 500,
        "sale_price_per_lot": 95000,
        "soft_costs_fixed": 120000,
        "contingency_pct": 0.1,
        "source": "test fixture",
    }
    parcels = []
    # fix-a / fix-b are large enough for generate_schemes to emit schemes;
    # fix-c is below the generator's viable scale (exercises no_schemes).
    for pid, (w, h) in (("fix-a", (400, 400)),
                        ("fix-b", (500, 300)),
                        ("fix-c", (100, 100))):
        parcels.append({
            "parcel_id": pid,
            "parcel_geojson": {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [square(w, h)]},
                "properties": {"parcel_id": pid, "crs": "local-feet"},
            },
            "zoning_config": dict(zoning),
            "finance_config": dict(finance),
        })
    manifest = {"max_schemes": 4, "parcels": parcels}
    mp = os.path.join(path, "fixture_manifest.json")
    with open(mp, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    return mp


class TestBenchmarkDeterminism(unittest.TestCase):
    def test_failure_table_byte_identical_across_runs(self):
        """Two harness runs on the same 3-parcel fixture must produce
        byte-identical failure_table.md (and findings/sample json)."""
        with tempfile.TemporaryDirectory() as td:
            manifest_path = _fixture_manifest(td)
            ids = ["fix-a", "fix-b", "fix-c"]
            out1 = os.path.join(td, "run1")
            out2 = os.path.join(td, "run2")
            s1 = run_benchmark(manifest_path, out1, sample_ids=ids)
            s2 = run_benchmark(manifest_path, out2, sample_ids=ids)
            self.assertEqual(s1["n_parcels"], 3)
            self.assertEqual(s2["n_parcels"], 3)
            for name in ("failure_table.md", "findings.json", "sample.json"):
                with open(os.path.join(out1, name), "rb") as f:
                    b1 = f.read()
                with open(os.path.join(out2, name), "rb") as f:
                    b2 = f.read()
                self.assertEqual(
                    b1, b2,
                    f"{name} differs between two identical harness runs",
                )
            # banner present in the markdown table
            with open(os.path.join(out1, "failure_table.md")) as f:
                text = f.read()
            self.assertIn("MACHINE-DRAFT EVALUATION", text)
            self.assertIn("NOT HUMAN VERIFICATION", text)

    def test_sample_covers_all_screen_districts(self):
        """The 30-parcel stratification must represent every district present
        in the real mass-screen manifest."""
        manifest_path = os.path.join(REPO_ROOT, "screen", "real_manifest.json")
        if not os.path.exists(manifest_path):
            self.skipTest("real manifest not present")
        with open(manifest_path) as f:
            manifest = json.load(f)
        district_of = {e["parcel_id"]: e["zoning_config"]["district"]
                       for e in manifest["parcels"]}
        all_districts = set(district_of.values())
        sample_districts = {district_of[s["parcel_id"]] for s in SAMPLE}
        self.assertEqual(len(SAMPLE), 30)
        self.assertEqual(sample_districts, all_districts,
                         "sample misses districts: "
                         f"{sorted(all_districts - sample_districts)}")
        # every sampled parcel carries a documented rationale
        for s in SAMPLE:
            self.assertTrue(s["rationale"], s["parcel_id"])


if __name__ == "__main__":
    unittest.main()
