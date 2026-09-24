"""Tests for the approved-plat benchmark harness.

No web, no invented data: these tests pin the harness's honesty properties —
unknown zoning never scores, tolerance math is exact, outputs are deterministic.
Run with the project venv python (imports prototype.pipeline -> shapely).
"""
import json
import os
import unittest

import harness

BASE = os.path.dirname(os.path.abspath(__file__))


class TestPlatsHonesty(unittest.TestCase):
    def test_every_entry_has_zoning_status(self):
        for p in harness.load_plats():
            self.assertIn(p["zoning"]["status"], ("known", "unknown"), p["plat_id"])

    def test_known_zoning_requires_cited_source_and_dims(self):
        for p in harness.load_plats():
            z = p["zoning"]
            if z["status"] == "known":
                for k in ("min_lot_area_sqft", "min_frontage_ft", "road_width_ft", "source"):
                    self.assertIn(k, z, f"{p['plat_id']} missing {k}")

    def test_unknown_zoning_never_enters_scored_set(self):
        for p in harness.load_plats():
            if p["zoning"]["status"] == "unknown":
                self.assertFalse(p.get("scored"), p["plat_id"])


class TestToleranceMath(unittest.TestCase):
    def _entry(self, approved):
        return {"plat_id": "x", "approved_lots": approved,
                "parent_polygon": "samples/mill_subdivision_parent.geojson",
                "zoning": {"status": "known"}}

    def test_within_15pct_boundary(self):
        # 4 approved: 4 -> err 0.0 pass; 5 -> err 0.25 fail
        for neron, approved, expected in [(4, 4, True), (5, 4, False), (17, 20, True), (16, 20, False)]:
            rel = abs(neron - approved) / approved
            self.assertEqual(rel <= harness.TOLERANCE, expected,
                             f"neron={neron} approved={approved}")

    def test_write_results_deterministic(self):
        # save the real results files so the test leaves no fake state behind
        real_json = open(os.path.join(BASE, "results.json")).read()
        real_md = open(os.path.join(BASE, "results.md")).read()
        results = [
            {"status": "scored", "plat_id": "a", "approved_lots": 10,
             "neron_top_ranked_lots": 11, "schemes": [], "relative_error": 0.1,
             "within_15pct": True, "zoning_source": "s"},
            {"status": "not_scored", "plat_id": "b", "approved_lots": None,
             "reason": "zoning unknown"},
        ]
        p1 = harness.write_results(results)
        with open(os.path.join(BASE, "results.json")) as f:
            blob1 = f.read()
        with open(os.path.join(BASE, "results.md")) as f:
            md1 = f.read()
        p2 = harness.write_results(results)
        with open(os.path.join(BASE, "results.json")) as f:
            blob2 = f.read()
        self.assertEqual(blob1, blob2)
        self.assertEqual(p1["pass_rate"], 1.0)
        self.assertTrue(p2["aim_met"])
        # restore the real results byte-for-byte (the scored set may be non-empty)
        with open(os.path.join(BASE, "results.json"), "w") as f:
            f.write(real_json)
        with open(os.path.join(BASE, "results.md"), "w") as f:
            f.write(real_md)
        with open(os.path.join(BASE, "results.md")) as f:
            md_restored = f.read()
        self.assertEqual(md_restored, real_md)  # sanity: restore actually rewrote


if __name__ == "__main__":
    unittest.main()
