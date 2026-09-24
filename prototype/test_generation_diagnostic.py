"""Tests for the scheme-generation diagnostic + two-pass fallback
(prototype/geometry.py plan_generation) and the pipeline's honest
no-schemes reporting.

Benchmark finding #1: the generator silently yielded 0 schemes on parcels
where conforming lots fit. These tests pin:
  - the primary pass is behavior-identical to historic generate_schemes()
    (goldens/demo/Jefferson must not move),
  - the fallback admits genuine 2-3 lot subdivisions only when the primary
    pass is empty and the parcel clears the size threshold,
  - every no-schemes result carries a machine-readable diagnostic naming
    the blocking reason,
  - per-scheme rulegraph applicable-rule counts are present in reports.

No human verdicts are produced or implied anywhere here.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from prototype import geometry
from prototype import pipeline as P
from rulegraph.engine import RuleGraph


def _square(w, h):
    return [[0.0, 0.0], [w, 0.0], [w, h], [0.0, h], [0.0, 0.0]]


R1_8 = {
    "district": "R-1-8",
    "min_lot_area_sqft": 8000,
    "min_frontage_ft": 70,
    "road_width_ft": 55,
}


class TestPlanGeneration(unittest.TestCase):
    def test_primary_path_identical_to_generate_schemes(self):
        """Parcels that succeed in the primary pass must be byte-identical
        to the historic generate_schemes() output (golden safety)."""
        coords = _square(400, 400)
        a = geometry.generate_schemes(coords, R1_8, "p", max_schemes=8)
        b, diag = geometry.plan_generation(coords, R1_8, "p", max_schemes=8)
        self.assertTrue(len(a) > 0)
        self.assertFalse(diag["fallback_used"])
        self.assertEqual(diag["verdict"], "schemes_found")
        self.assertEqual(
            [s.fingerprint for s in a], [s.fingerprint for s in b]
        )

    def test_fallback_admits_small_subdivision(self):
        """A parcel fitting ~2.5 min-lots yields 2-lot schemes via the
        fallback that the historic >=4 filter discarded."""
        zoning = dict(R1_8, min_lot_area_sqft=8000)
        # 200x200 = 40000 sqft = 5x min area; spine road leaves room for ~2 lots
        coords = _square(200, 200)
        primary = geometry.generate_schemes(coords, zoning, "p", max_schemes=8)
        schemes, diag = geometry.plan_generation(coords, zoning, "p", max_schemes=8)
        # primary may or may not find schemes; the diagnostic must be honest either way
        if not primary:
            self.assertTrue(diag["fallback_used"])
            self.assertGreater(len(schemes), 0)
            self.assertTrue(all(len(s.lots) >= 2 for s in schemes))
            self.assertEqual(diag["verdict"], "schemes_found")
        else:
            self.assertFalse(diag["fallback_used"])

    def test_below_size_threshold_no_fallback(self):
        """A parcel too small to subdivide gets an honest below-threshold
        verdict, not a fallback attempt."""
        coords = _square(60, 60)  # 3600 sqft < 2x8000
        schemes, diag = geometry.plan_generation(coords, R1_8, "p")
        self.assertEqual(schemes, [])
        self.assertFalse(diag["fallback_used"])
        self.assertEqual(diag["verdict"], "no_schemes__below_size_threshold")
        self.assertIn("fallback_skipped_reason", diag)

    def test_reason_codes_cover_silent_paths(self):
        """Every historic silent-None path now has a named reason code."""
        # tiny parcel: every candidate hits parcel_too_small_for_config
        coords = _square(60, 60)
        _schemes, diag = geometry.plan_generation(coords, R1_8, "p")
        reasons = diag["primary_blocking_reasons"]
        self.assertIn(geometry.REASON_PARCEL_TOO_SMALL, reasons)
        self.assertEqual(diag["top_blocking_reason"], geometry.REASON_PARCEL_TOO_SMALL)

    def test_diagnostic_is_deterministic(self):
        coords = _square(300, 210)
        _, d1 = geometry.plan_generation(coords, R1_8, "p", max_schemes=8)
        _, d2 = geometry.plan_generation(coords, R1_8, "p", max_schemes=8)
        self.assertEqual(d1, d2)

    def test_unexpected_verdict_when_large_parcel_fails(self):
        """A large parcel that still yields nothing is flagged loud."""
        # extremely narrow ribbon: area is large but no conforming lots fit
        coords = [[0.0, 0.0], [2000.0, 0.0], [2000.0, 30.0], [0.0, 30.0], [0.0, 0.0]]
        schemes, diag = geometry.plan_generation(coords, R1_8, "p")
        self.assertEqual(schemes, [])
        self.assertEqual(diag["verdict"], "no_schemes__unexpected")
        self.assertGreater(diag["area_min_lot_ratio"], 2.0)


class TestPipelineDiagnostic(unittest.TestCase):
    def _run(self, coords, zoning):
        td = tempfile.mkdtemp(prefix="gen_diag_test_")
        parcel_path = os.path.join(td, "parcel.geojson")
        zoning_path = os.path.join(td, "zoning.json")
        finance_path = os.path.join(td, "finance.json")
        with open(parcel_path, "w") as f:
            json.dump({"type": "Polygon", "coordinates": [coords],
                       "properties": {"parcel_id": "T", "crs": "local-feet"}}, f)
        with open(zoning_path, "w") as f:
            json.dump(zoning, f)
        with open(finance_path, "w") as f:
            json.dump({"road_cost_per_lf": 500, "sale_price_per_lot": 95000,
                       "soft_costs_fixed": 120000, "contingency_pct": 0.1,
                       "source": "test"}, f)
        return P.run_pipeline(parcel_path, zoning_path, finance_path,
                              os.path.join(td, "out"), max_schemes=4)["report"]

    def test_report_carries_scheme_generation_block(self):
        report = self._run(_square(60, 60), R1_8)
        self.assertEqual(report["status"], "no_schemes_generated")
        gen = report["scheme_generation"]
        self.assertEqual(gen["verdict"], "no_schemes__below_size_threshold")
        self.assertEqual(gen["strategy"], "spine_road")
        self.assertIn("top_blocking_reason", gen)

    def test_report_carries_applicable_counts(self):
        report = self._run(_square(400, 400), R1_8)
        self.assertEqual(report["status"], "ok")
        for s in report["schemes"]:
            self.assertIn("rulegraph_applicable_rules", s)
            self.assertIsInstance(s["rulegraph_applicable_rules"], int)
            # cross-check against the per-rule list
            counted = sum(1 for r in s["rulegraph"] if r.get("applicable") is True)
            self.assertEqual(s["rulegraph_applicable_rules"], counted)

    def test_note_distinguishes_vacuous_pass(self):
        report = self._run(_square(400, 400), R1_8)
        note = report["rulegraph"]["note"]
        self.assertIn("no applicable verified rules", note)
        self.assertIn("rulegraph_applicable_rules", note)


class TestSchemeVerdictApplicableCount(unittest.TestCase):
    def test_applicable_count_present(self):
        g = RuleGraph.load(os.path.join(REPO_ROOT, "rulegraph", "verified_rules.json"))
        v = g.scheme_verdict({"district": "M-1"})
        self.assertIn("applicable_count", v)
        # Canonical store: 6 M-1 rules scope in; with no yard facts every
        # yard-dependent evaluation is UNKNOWN (honest, never defaulted).
        self.assertEqual(v["applicable_count"], 6)
        self.assertEqual(v["verdict"], "UNKNOWN")

    def test_applicable_count_counts_district_match(self):
        g = RuleGraph.load(os.path.join(REPO_ROOT, "rulegraph", "verified_rules.json"))
        v = g.scheme_verdict({"district": "MU-11"})
        self.assertGreater(v["applicable_count"], 0)


if __name__ == "__main__":
    unittest.main()
