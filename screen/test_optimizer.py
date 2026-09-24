"""Tests for screen/optimizer.py.

Covers: the hard zero-FAIL filter (a rule-failing candidate is never
selected even when it ties on profit), UNKNOWN-penalty monotonicity, and
byte-identical determinism of sweep.csv across runs.
"""
import csv
import json
import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from screen import optimizer as opt
from prototype.economics import finance_config_from_economics, load_economics

ECON_PATH = os.path.join(REPO_ROOT, "inputs", "economics_slco_2026.json")


def _rect_parcel_geojson(parcel_id, w=200.0, h=300.0):
    return {
        "type": "Feature",
        "properties": {"parcel_id": parcel_id},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [w, 0], [w, h], [0, h], [0, 0]]],
        },
    }


def _zoning(district, area=5000, front=50, road=50):
    return {
        "district": district,
        "zone_label": f"{district} test zoning (DRAFT)",
        "min_lot_area_sqft": area,
        "min_frontage_ft": front,
        "road_width_ft": road,
    }


def _finance(district):
    econ = load_economics(ECON_PATH)
    return finance_config_from_economics(econ, district, ECON_PATH)


class TestObjective(unittest.TestCase):
    def test_unknown_penalty_monotonic_positive_profit(self):
        vals = [opt.risk_adjusted_profit(1000.0, u, 8) for u in range(9)]
        for a, b in zip(vals, vals[1:]):
            self.assertLess(b, a)  # strictly decreasing in unknowns

    def test_unknown_penalty_monotonic_negative_profit(self):
        # Money-losing candidates: more UNKNOWNs must make it *worse*
        # (more negative), never better.
        vals = [opt.risk_adjusted_profit(-1000.0, u, 8) for u in range(9)]
        for a, b in zip(vals, vals[1:]):
            self.assertLess(b, a)

    def test_unknown_penalty_zero_profit(self):
        for u in range(9):
            self.assertEqual(opt.risk_adjusted_profit(0.0, u, 8), 0.0)

    def test_penalty_bounds(self):
        p = 1000.0
        self.assertEqual(opt.risk_adjusted_profit(p, 0, 8), p)
        self.assertAlmostEqual(opt.risk_adjusted_profit(p, 8, 8), p * 0.9)
        # k=0 disables the penalty entirely
        self.assertEqual(opt.risk_adjusted_profit(p, 8, 8, k=0.0), p)
        # unknown values are never treated as passed: penalty is one-sided
        self.assertLess(opt.risk_adjusted_profit(p, 1, 8), p)


class TestGrid(unittest.TestCase):
    def test_grid_contains_exact_baseline_point(self):
        z = _zoning("M-1", area=20000, front=100, road=60)
        pts = opt.grid_points(z)
        self.assertEqual(len(pts), 27)
        base = [p for p in pts
                if p["area_mult"] == 1.0 and p["frontage_mult"] == 1.0
                and p["road_width_ft"] == 60.0]
        self.assertEqual(len(base), 1)
        self.assertEqual(base[0]["min_lot_area_sqft"], 20000)
        self.assertEqual(base[0]["min_frontage_ft"], 100)

    def test_program_variants_none_first_tower_only_where_sensitive(self):
        mu11 = opt.program_variants("MU-11")
        self.assertEqual([n for n, _ in mu11],
                         ["none", "draft-lowrise", "draft-tower"])
        self.assertIsNone(mu11[0][1])
        m1 = opt.program_variants("M-1")
        self.assertEqual([n for n, _ in m1], ["none", "draft-lowrise"])
        pl = opt.program_variants("PL")
        self.assertIn("draft-tower", [n for n, _ in pl])

    def test_pick_winner_tiebreaks(self):
        def row(ra, profit, unknowns):
            return {"eligible": "true", "risk_adjusted_profit": ra,
                    "profit": profit, "rg_unknown": unknowns}
        # higher risk-adjusted wins
        w = opt.pick_winner([row("1.00", "5.00", 0), row("2.00", "1.00", 9)])
        self.assertEqual(w["profit"], "1.00")
        # tie on risk-adjusted -> higher raw profit
        w = opt.pick_winner([row("2.00", "5.00", 0), row("2.00", "9.00", 0)])
        self.assertEqual(w["profit"], "9.00")
        # tie on both -> fewer unknowns
        w = opt.pick_winner([row("2.00", "9.00", 3), row("2.00", "9.00", 1)])
        self.assertEqual(w["rg_unknown"], 1)
        # full tie -> earlier grid order
        r1, r2 = row("2.00", "9.00", 1), row("2.00", "9.00", 1)
        self.assertIs(opt.pick_winner([r1, r2]), r1)
        self.assertIs(opt.pick_winner([r2, r1]), r2)
        # ineligible rows never win
        bad = dict(row("999.00", "999.00", 0), eligible="false")
        self.assertIs(opt.pick_winner([bad, r1]), r1)
        self.assertIsNone(opt.pick_winner([bad]))


class TestFailFilter(unittest.TestCase):
    """The naive-profit-max candidate may fail a rule; it must never win."""

    def test_tower_candidate_never_selected(self):
        entry = {
            "parcel_id": "TEST-MU11-FAIL",
            "parcel_geojson": _rect_parcel_geojson("TEST-MU11-FAIL"),
            "zoning_config": _zoning("MU-11"),
        }
        # Tower FIRST: a naive first-max-profit selector would take it, since
        # the program does not change profit — only RuleGraph outcomes.
        order = [("draft-tower", opt._draft_tower()),
                 ("none", None),
                 ("draft-lowrise", opt._draft_lowrise())]
        with tempfile.TemporaryDirectory() as tmp:
            rows, winner = opt.optimize_parcel(
                entry, tmp, _finance("MU-11"), max_schemes=2,
                program_order=order)
        tower_rows = [r for r in rows if r["program"] == "draft-tower"]
        self.assertTrue(tower_rows, "expected tower candidates in the sweep")
        for r in tower_rows:
            self.assertEqual(r["eligible"], "false")
            self.assertIn("rg_fail", r["ineligible_reason"])
            self.assertGreater(int(r["rg_fail"]), 0)
        self.assertTrue(winner, "expected an eligible winner")
        self.assertEqual(winner["eligible"], "true")
        self.assertEqual(int(winner["rg_fail"]), 0)
        self.assertNotEqual(winner["program"], "draft-tower")
        # lowrise (0 UNKNOWNs) beats none (6 UNKNOWNs) at identical profit
        self.assertEqual(winner["program"], "draft-lowrise")


class TestDeterminism(unittest.TestCase):
    def test_two_runs_byte_identical_sweep_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = os.path.join(tmp, "manifest.json")
            baseline_path = os.path.join(tmp, "baseline.csv")
            entry = {
                "parcel_id": "TEST-DET-001",
                "parcel_geojson": _rect_parcel_geojson("TEST-DET-001"),
                "zoning_config": _zoning("M-1"),
            }
            with open(manifest_path, "w") as f:
                json.dump({"screen_name": "det-test", "max_schemes": 2,
                           "parcels": [entry]}, f)
            with open(baseline_path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["parcel_id", "zone_label", "district", "row_kind",
                            "scheme_id", "lots", "road_ft", "revenue",
                            "total_cost", "profit", "margin", "rg_verdict",
                            "rg_pass", "rg_fail", "rg_unknown",
                            "geometry_clean", "unknowns_count", "error"])
                w.writerow(["TEST-DET-001", "M-1 test", "M-1", "scheme",
                            "scheme_00", "4", "100.0", "1800000.0",
                            "200000.0", "1600000.0", "0.8889", "PASS",
                            8, 0, 0, "true", 0, ""])
            outs = []
            for i in range(2):
                out = os.path.join(tmp, f"out{i}")
                opt.optimize_manifest(manifest_path, baseline_path, ECON_PATH,
                                      out, max_schemes=2)
                outs.append(out)
            for name in ("sweep.csv", "best.csv"):
                with open(os.path.join(outs[0], name), "rb") as f:
                    a = f.read()
                with open(os.path.join(outs[1], name), "rb") as f:
                    b = f.read()
                self.assertEqual(a, b, f"{name} differs between runs")
                self.assertTrue(a, f"{name} is empty")


if __name__ == "__main__":
    unittest.main()
