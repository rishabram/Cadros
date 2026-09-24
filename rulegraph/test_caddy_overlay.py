"""Tests for the Caddy extraction v1 param overlay.

Run: venv/bin/python -m unittest rulegraph.test_caddy_overlay -v

The overlay (rulegraph/caddy_params_v1.json) makes 10 stored-but-not-
executable M-1/OS/PL rules executable WITHOUT editing the canonical store:
fingerprint, rule ids, and human_verification records are untouched.
M-1-06 and OS-05 are qualitative gaps -> no evaluator -> stay UNKNOWN.
"""
import json
import unittest

from .engine import RuleGraph

RULES_PATH = "rulegraph/verified_rules.json"
OVERLAY_PATH = "rulegraph/caddy_params_v1.json"
PINNED_FINGERPRINT = "9cc91ac71f5f1de221b9609291ce264ca33d6c6ba9b98f7e7f898778fd0cfd1c"

OVERLAID = ["M-1-01", "M-1-03", "M-1-04", "M-1-05",
            "OS-02", "OS-03", "OS-04",
            "PL-01", "PL-02", "PL-03"]
STILL_NO_EVALUATOR = ["M-1-06", "OS-05"]


def lots(*specs):
    return [{"lot_id": f"L{i}", "area_sqft": a, "frontage_ft": w}
            for i, (a, w) in enumerate(specs)]


class TestOverlayMechanics(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=OVERLAY_PATH)

    def test_fingerprint_untouched_by_overlay(self):
        self.assertEqual(self.g.fingerprint, PINNED_FINGERPRINT)

    def test_store_file_still_has_no_evaluator_or_params(self):
        with open(RULES_PATH) as f:
            store = json.load(f)
        by_id = {r["rule_id"]: r for r in store["rules"]}
        for rid in OVERLAID:
            self.assertIsNone(by_id[rid].get("evaluator"), rid)
            self.assertIsNone(by_id[rid].get("params"), rid)

    def test_human_verification_records_untouched(self):
        for rid in OVERLAID + STILL_NO_EVALUATOR:
            hv = self.g.rules[rid].get("human_verification") or {}
            self.assertEqual(hv.get("result"), "VERIFIED", rid)
            self.assertTrue(hv.get("verified_by"), rid)

    def test_overlay_covers_exactly_ten_rules(self):
        self.assertEqual(sorted(self.g.overlays), sorted(OVERLAID))

    def test_params_source_label_on_overlay_results(self):
        r = self.g.evaluate("M-1-01",
                            {"district": "M-1",
                             "scheme_lots": lots((20000, 100))})
        self.assertIn("caddy_extraction_v1", r["reason"])
        self.assertIn("not a human verdict", r["reason"])

    def test_qualitative_gaps_still_have_no_evaluator(self):
        districts = {"M-1-06": "M-1", "OS-05": "OS"}
        for rid in STILL_NO_EVALUATOR:
            r = self.g.evaluate(rid, {"district": districts[rid]})
            self.assertEqual(r["outcome"], "UNKNOWN", rid)
            self.assertIn("no evaluator registered", r["reason"], rid)
            self.assertTrue(r["applicable"], rid)

    def test_overlay_missing_file_is_loud(self):
        with self.assertRaises(FileNotFoundError):
            RuleGraph.load(RULES_PATH, overlay_path="rulegraph/nope.json")


class TestM101(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=OVERLAY_PATH)

    def ev(self, ctx):
        return self.g.evaluate("M-1-01", dict({"district": "M-1"}, **ctx))

    def test_all_conforming_pass(self):
        r = self.ev({"scheme_lots": lots((20000, 100), (15000, 80))})
        self.assertEqual(r["outcome"], "PASS")

    def test_below_minimum_is_unknown_not_fail(self):
        # The quote's existing-lot clause (conforming if existing as of
        # 1995-04-12) could apply; existing status is not in the context.
        r = self.ev({"scheme_lots": lots((9000, 100))})
        self.assertEqual(r["outcome"], "UNKNOWN")
        self.assertIn("1995-04-12", r["reason"])

    def test_below_width_is_unknown_not_fail(self):
        r = self.ev({"scheme_lots": lots((20000, 70))})
        self.assertEqual(r["outcome"], "UNKNOWN")

    def test_no_lot_facts_is_unknown(self):
        r = self.ev({})
        self.assertEqual(r["outcome"], "UNKNOWN")


class TestM103(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=OVERLAY_PATH)

    def ev(self, **ctx):
        return self.g.evaluate("M-1-03", dict({"district": "M-1"}, **ctx))

    def test_height_at_or_below_30_passes_regardless(self):
        r = self.ev(height_ft=30)
        self.assertEqual(r["outcome"], "PASS")

    def test_not_abutting_passes(self):
        r = self.ev(height_ft=50, abuts_zones_side=["M-2"],
                    abuts_zones_rear=[])
        self.assertEqual(r["outcome"], "PASS")

    def test_abutment_unknown_is_unknown(self):
        r = self.ev(height_ft=50)
        self.assertEqual(r["outcome"], "UNKNOWN")

    def test_abutting_tall_buffer_gap_is_unknown(self):
        # Buffer depth is a recorded extraction gap: required total cannot
        # be computed -> UNKNOWN, never a guessed PASS/FAIL.
        r = self.ev(height_ft=50, abuts_zones_side=["AG-2"],
                    front_setback_ft=40)
        self.assertEqual(r["outcome"], "UNKNOWN")
        self.assertIn("gap", r["reason"])

    def test_height_unknown_is_unknown(self):
        r = self.ev(abuts_zones_side=["AG-5"])
        self.assertEqual(r["outcome"], "UNKNOWN")


class TestM104(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=OVERLAY_PATH)

    def ev(self, **ctx):
        return self.g.evaluate("M-1-04", dict({"district": "M-1"}, **ctx))

    def test_within_base_passes(self):
        self.assertEqual(self.ev(height_ft=65)["outcome"], "PASS")

    def test_above_base_non_column_fails(self):
        r = self.ev(height_ft=70, is_distillation_column_structure=False)
        self.assertEqual(r["outcome"], "FAIL")

    def test_above_base_column_status_unknown(self):
        r = self.ev(height_ft=70)
        self.assertEqual(r["outcome"], "UNKNOWN")

    def test_column_within_faa_passes(self):
        r = self.ev(height_ft=100, is_distillation_column_structure=True,
                    faa_max_elevation_ft=110)
        self.assertEqual(r["outcome"], "PASS")

    def test_column_faa_unknown_is_unknown(self):
        r = self.ev(height_ft=100, is_distillation_column_structure=True)
        self.assertEqual(r["outcome"], "UNKNOWN")

    def test_above_120_absolute_fails(self):
        r = self.ev(height_ft=121, is_distillation_column_structure=True,
                    faa_max_elevation_ft=200)
        self.assertEqual(r["outcome"], "FAIL")


class TestM105(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=OVERLAY_PATH)

    def ev(self, **ctx):
        return self.g.evaluate("M-1-05", dict({"district": "M-1"}, **ctx))

    def test_within_base_passes_no_zone_needed(self):
        self.assertEqual(self.ev(height_ft=60)["outcome"], "PASS")

    def test_above_85_absolute_fails(self):
        r = self.ev(height_ft=86, in_m1_height_exception_zone=True,
                    design_review_completed=True)
        self.assertEqual(r["outcome"], "FAIL")

    def test_zone_and_design_review_pass(self):
        r = self.ev(height_ft=80, in_m1_height_exception_zone=True,
                    design_review_completed=True)
        self.assertEqual(r["outcome"], "PASS")

    def test_zone_known_no_design_review_fails(self):
        r = self.ev(height_ft=80, in_m1_height_exception_zone=True,
                    design_review_completed=False)
        self.assertEqual(r["outcome"], "FAIL")

    def test_not_in_zone_fails(self):
        r = self.ev(height_ft=80, in_m1_height_exception_zone=False)
        self.assertEqual(r["outcome"], "FAIL")

    def test_zone_unknown_is_unknown(self):
        r = self.ev(height_ft=80)
        self.assertEqual(r["outcome"], "UNKNOWN")


class TestOS02(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=OVERLAY_PATH)

    def ev(self, ctx):
        return self.g.evaluate("OS-02", dict({"district": "OS"}, **ctx))

    def test_small_lot_within_35_passes(self):
        r = self.ev({"scheme_lots": lots((3 * 43560, 200)),
                     "height_ft": 35})
        self.assertEqual(r["outcome"], "PASS")

    def test_small_lot_above_35_fails(self):
        r = self.ev({"scheme_lots": lots((3 * 43560, 200)),
                     "height_ft": 36})
        self.assertEqual(r["outcome"], "FAIL")

    def test_large_lot_45_60_needs_design_review(self):
        base = {"scheme_lots": lots((5 * 43560, 200)), "height_ft": 50}
        r = self.ev(dict(base, design_review_completed=True))
        self.assertEqual(r["outcome"], "PASS")
        r = self.ev(dict(base, design_review_completed=False))
        self.assertEqual(r["outcome"], "FAIL")
        r = self.ev(base)
        self.assertEqual(r["outcome"], "UNKNOWN")

    def test_above_60_fails_even_with_review(self):
        r = self.ev({"scheme_lots": lots((5 * 43560, 200)), "height_ft": 61,
                     "design_review_completed": True})
        self.assertEqual(r["outcome"], "FAIL")

    def test_public_utilities_exempt(self):
        r = self.ev({"scheme_lots": lots((3 * 43560, 200)), "height_ft": 50,
                     "is_slc_public_utilities_structure": True})
        self.assertEqual(r["outcome"], "PASS")

    def test_height_unknown_is_unknown(self):
        r = self.ev({"scheme_lots": lots((3 * 43560, 200))})
        self.assertEqual(r["outcome"], "UNKNOWN")


class TestOS03(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=OVERLAY_PATH)

    def ev(self, **ctx):
        return self.g.evaluate("OS-03", dict({"district": "OS"}, **ctx))

    def test_no_equipment_passes(self):
        self.assertEqual(
            self.ev(has_recreation_equipment=False)["outcome"], "PASS")

    def test_unknown_equipment_is_unknown(self):
        self.assertEqual(self.ev()["outcome"], "UNKNOWN")

    def test_within_80_passes(self):
        r = self.ev(has_recreation_equipment=True,
                    recreation_equipment_height_ft=80)
        self.assertEqual(r["outcome"], "PASS")

    def test_above_80_fails(self):
        r = self.ev(has_recreation_equipment=True,
                    recreation_equipment_height_ft=81)
        self.assertEqual(r["outcome"], "FAIL")


class TestOS04(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=OVERLAY_PATH)

    def base(self, **kw):
        ctx = {"district": "OS",
               "scheme_lots": lots((3 * 43560, 200)),
               "height_ft": 15,
               "front_setback_ft": 12, "corner_side_setback_ft": 12,
               "interior_side_setback_ft": 12, "rear_setback_ft": 12}
        ctx.update(kw)
        return ctx

    def test_conforming_passes(self):
        self.assertEqual(
            self.g.evaluate("OS-04", self.base())["outcome"], "PASS")

    def test_setback_unknown_is_unknown(self):
        ctx = self.base()
        del ctx["front_setback_ft"]
        self.assertEqual(
            self.g.evaluate("OS-04", ctx)["outcome"], "UNKNOWN")

    def test_below_base_minimum_fails(self):
        ctx = self.base(front_setback_ft=9)
        r = self.g.evaluate("OS-04", ctx)
        self.assertEqual(r["outcome"], "FAIL")

    def test_inflation_applies_over_20ft_on_small_lot(self):
        # 25 ft height on <= 4 ac: +5 ft inflation -> front needs 15.
        ctx = self.base(height_ft=25, front_setback_ft=14)
        r = self.g.evaluate("OS-04", ctx)
        self.assertEqual(r["outcome"], "FAIL")
        self.assertIn("inflation", r["reason"])
        ctx = self.base(height_ft=25, front_setback_ft=15,
                        corner_side_setback_ft=15,
                        interior_side_setback_ft=15, rear_setback_ft=15)
        self.assertEqual(
            self.g.evaluate("OS-04", ctx)["outcome"], "PASS")

    def test_large_lot_15ft_interior(self):
        ctx = self.base()
        ctx["scheme_lots"] = lots((5 * 43560, 200))
        ctx["interior_side_setback_ft"] = 14
        r = self.g.evaluate("OS-04", ctx)
        self.assertEqual(r["outcome"], "FAIL")


class TestPL01(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=OVERLAY_PATH)

    def ev(self, ctx):
        return self.g.evaluate("PL-01", dict({"district": "PL"}, **ctx))

    def test_use_unknown_is_unknown(self):
        r = self.ev({"scheme_lots": lots((6 * 43560, 200))})
        self.assertEqual(r["outcome"], "UNKNOWN")

    def test_school_conforming_passes(self):
        r = self.ev({"proposed_use_is_public_school": True,
                     "scheme_lots": lots((6 * 43560, 160))})
        self.assertEqual(r["outcome"], "PASS")

    def test_school_below_5ac_fails(self):
        r = self.ev({"proposed_use_is_public_school": True,
                     "scheme_lots": lots((4 * 43560, 160))})
        self.assertEqual(r["outcome"], "FAIL")

    def test_other_use_row(self):
        r = self.ev({"proposed_use_is_public_school": False,
                     "scheme_lots": lots((21000, 80))})
        self.assertEqual(r["outcome"], "PASS")
        r = self.ev({"proposed_use_is_public_school": False,
                     "scheme_lots": lots((19000, 80))})
        self.assertEqual(r["outcome"], "FAIL")


class TestPL02(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=OVERLAY_PATH)

    def ev(self, **ctx):
        return self.g.evaluate("PL-02", dict({"district": "PL"}, **ctx))

    def test_at_or_below_35_passes_regardless_of_use(self):
        self.assertEqual(self.ev(height_ft=35)["outcome"], "PASS")

    def test_other_use_above_35_fails(self):
        r = self.ev(height_ft=36, proposed_use_is_public_school=False,
                    proposed_use_pl_civic_listed=False)
        self.assertEqual(r["outcome"], "FAIL")

    def test_k12_within_125_passes(self):
        r = self.ev(height_ft=125, proposed_use_is_public_school=True)
        self.assertEqual(r["outcome"], "PASS")

    def test_k12_above_125_fails(self):
        r = self.ev(height_ft=126, proposed_use_is_public_school=True)
        self.assertEqual(r["outcome"], "FAIL")

    def test_civic_above_75_abutment_gap_is_unknown(self):
        r = self.ev(height_ft=76, proposed_use_is_public_school=False,
                    proposed_use_pl_civic_listed=True)
        self.assertEqual(r["outcome"], "UNKNOWN")
        self.assertIn("gap", r["reason"])

    def test_use_unknown_above_35_is_unknown(self):
        r = self.ev(height_ft=40)
        self.assertEqual(r["outcome"], "UNKNOWN")


class TestPL03(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=OVERLAY_PATH)

    def base(self, **kw):
        ctx = {"district": "PL", "proposed_use_is_public_school": True,
               "front_setback_ft": 30, "corner_side_setback_ft": 30,
               "interior_side_setback_ft": 50, "rear_setback_ft": 50,
               "abuts_zones_side": ["R-1"], "abuts_zones_rear": ["M-1"]}
        ctx.update(kw)
        return ctx

    def test_k12_next_to_residential_passes(self):
        self.assertEqual(
            self.g.evaluate("PL-03", self.base())["outcome"], "PASS")

    def test_k12_below_50_next_to_residential_fails(self):
        ctx = self.base(interior_side_setback_ft=49)
        r = self.g.evaluate("PL-03", ctx)
        self.assertEqual(r["outcome"], "FAIL")

    def test_k12_next_to_other_district_30(self):
        ctx = self.base(abuts_zones_side=["MU-5"],
                        interior_side_setback_ft=30)
        self.assertEqual(
            self.g.evaluate("PL-03", ctx)["outcome"], "PASS")

    def test_unmapped_zone_is_unknown(self):
        ctx = self.base(abuts_zones_side=["ZZ-9"])
        r = self.g.evaluate("PL-03", ctx)
        self.assertEqual(r["outcome"], "UNKNOWN")

    def test_use_unknown_is_unknown(self):
        ctx = self.base()
        del ctx["proposed_use_is_public_school"]
        self.assertEqual(
            self.g.evaluate("PL-03", ctx)["outcome"], "UNKNOWN")

    def test_other_uses_row(self):
        ctx = self.base(proposed_use_is_public_school=False,
                        front_setback_ft=30, corner_side_setback_ft=30,
                        interior_side_setback_ft=20, rear_setback_ft=30)
        self.assertEqual(
            self.g.evaluate("PL-03", ctx)["outcome"], "PASS")


if __name__ == "__main__":
    unittest.main()
