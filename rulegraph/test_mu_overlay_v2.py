"""Tests for the Caddy extraction v2 param overlay (MU numeric params).

Run: venv/bin/python -m unittest rulegraph.test_mu_overlay_v2 -v

The overlay (rulegraph/caddy_params_v2.json) makes 32 stored-but-not-
executable MU rules executable WITHOUT editing the canonical store:
fingerprint, rule ids, and human_verification records are untouched.
Package-3's explicit gaps stay gaps (UNKNOWN) — never zeros or defaults.
"""
import json
import os
import tempfile
import unittest

from .engine import RuleGraph

RULES_PATH = "rulegraph/verified_rules.json"
OVERLAY_V1 = "rulegraph/caddy_params_v1.json"
OVERLAY_V2 = "rulegraph/caddy_params_v2.json"
PINNED_FINGERPRINT = "9cc91ac71f5f1de221b9609291ce264ca33d6c6ba9b98f7e7f898778fd0cfd1c"

V2_RULES = [
    "MU-5-01", "MU-5-02", "MU-5-03", "MU-5-04", "MU-5-05", "MU-5-06",
    "MU-5-07", "MU-5-08", "MU-5-10", "MU-5-11", "MU-5-12", "MU-5-13",
    "MU-5-14", "MU-5-15",
    "MU-6-01", "MU-6-02", "MU-6-03", "MU-6-04", "MU-6-05", "MU-6-06",
    "MU-6-07", "MU-6-08", "MU-6-10", "MU-6-11", "MU-6-12", "MU-6-13",
    "MU-6-14", "MU-6-15",
    "MU-11-01", "MU-11-02", "MU-11-03", "MU-11-04",
]
# MU rules the overlay deliberately leaves without an evaluator
# (uses-per-story semantics or site-plan-only geometry).
STILL_NO_EVALUATOR = ["MU-5-09", "MU-6-09", "MU-OPENSPACE-01"]
# MU-11-06..10 already have structured canonical evaluators; v2 must not
# replace them merely because Package 3 repeats the same numbers.
STORE_EXECUTABLE = ["MU-11-05", "MU-11-06", "MU-11-07", "MU-11-08",
                    "MU-11-09", "MU-11-10", "MU-11-11"]

URBAN = "urban_house"
ROW = "row_house"
MF = "multifamily_residential"


class TestOverlayV2Mechanics(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=[OVERLAY_V1, OVERLAY_V2])

    def test_fingerprint_untouched_by_v2(self):
        self.assertEqual(self.g.fingerprint, PINNED_FINGERPRINT)

    def test_store_file_still_has_no_evaluator_or_params(self):
        with open(RULES_PATH) as f:
            store = json.load(f)
        by_id = {r["rule_id"]: r for r in store["rules"]}
        for rid in V2_RULES:
            self.assertIsNone(by_id[rid].get("evaluator"), rid)
            self.assertIsNone(by_id[rid].get("params"), rid)

    def test_human_verification_records_untouched(self):
        for rid in V2_RULES[:6] + STILL_NO_EVALUATOR:
            hv = self.g.rules[rid].get("human_verification") or {}
            self.assertEqual(hv.get("result"), "VERIFIED", rid)
            self.assertTrue(hv.get("verified_by"), rid)

    def test_v2_covers_exactly_32_rules(self):
        g2 = RuleGraph.load(RULES_PATH, overlay_path=OVERLAY_V2)
        self.assertEqual(sorted(g2.overlays), sorted(V2_RULES))

    def test_both_overlays_union(self):
        self.assertEqual(len(self.g.overlays), 10 + 32)

    def test_params_source_labels(self):
        r1 = self.g.evaluate("M-1-01",
                             {"district": "M-1",
                              "scheme_lots": [{"lot_id": "L0", "area_sqft": 20000,
                                               "frontage_ft": 100}]})
        self.assertIn("caddy_extraction_v1", r1["reason"])
        r2 = self.g.evaluate("MU-5-01",
                             {"district": "MU-5", "building_form": URBAN,
                              "height_ft": 35})
        self.assertIn("caddy_extraction_v2", r2["reason"])
        self.assertIn("not a human verdict", r2["reason"])
        self.assertNotIn("caddy_extraction_v1", r2["reason"])

    def test_v1_reasons_byte_identical_with_v2_loaded(self):
        """Adding the v2 overlay must not perturb any v1-overlay result."""
        g1 = RuleGraph.load(RULES_PATH, overlay_path=OVERLAY_V1)
        ctx = {"district": "M-1",
               "scheme_lots": [{"lot_id": "L0", "area_sqft": 20000,
                                "frontage_ft": 100}]}
        for rid in ["M-1-01", "M-1-03", "M-1-04", "M-1-05",
                    "OS-02", "OS-03", "OS-04", "PL-01", "PL-02", "PL-03"]:
            a = g1.evaluate(rid, dict(ctx))
            b = self.g.evaluate(rid, dict(ctx))
            self.assertEqual(a["outcome"], b["outcome"], rid)
            self.assertEqual(a["reason"], b["reason"], rid)

    def test_store_executable_mu11_not_overridden_by_v2(self):
        # MU-11-06..10 keep their structured canonical evaluators; v2 names
        # no rule already carrying store params.
        with open(RULES_PATH) as f:
            store = json.load(f)
        by_id = {r["rule_id"]: r for r in store["rules"]}
        v2doc = json.load(open(OVERLAY_V2))
        for rid in STORE_EXECUTABLE:
            self.assertTrue(by_id[rid].get("evaluator"), rid)
            self.assertNotIn(rid, v2doc["rules"], rid)
        r = self.g.evaluate("MU-11-06",
                            {"district": "MU-11", "building_form": ROW,
                             "height_ft": 45})
        self.assertNotIn("caddy_extraction_v2", r["reason"])

    def test_later_overlay_wins_on_conflict(self):
        doc_a = {"params_source_tag": "tag_a",
                 "rules": {"MU-5-01": {"evaluator": "mu_max_height",
                                       "params": {"applies_to_forms": [URBAN],
                                                  "max_ft": 40}}}}
        doc_b = {"params_source_tag": "tag_b",
                 "rules": {"MU-5-01": {"evaluator": "mu_max_height",
                                       "params": {"applies_to_forms": [URBAN],
                                                  "max_ft": 99}}}}
        with tempfile.TemporaryDirectory() as d:
            pa, pb = os.path.join(d, "a.json"), os.path.join(d, "b.json")
            json.dump(doc_a, open(pa, "w"))
            json.dump(doc_b, open(pb, "w"))
            g = RuleGraph.load(RULES_PATH, overlay_path=[pa, pb])
            r = g.evaluate("MU-5-01",
                           {"district": "MU-5", "building_form": URBAN,
                            "height_ft": 50})
            self.assertEqual(r["outcome"], "PASS")  # 50 <= 99, not <= 40
            self.assertIn("tag_b", r["reason"])

    def test_overlay_missing_file_is_loud(self):
        with self.assertRaises(FileNotFoundError):
            RuleGraph.load(RULES_PATH,
                           overlay_path=[OVERLAY_V2, "rulegraph/nope.json"])

    def test_overlay_unknown_rule_is_loud(self):
        doc = {"params_source_tag": "tag_x",
               "rules": {"MU-5-01": {"evaluator": "mu_max_height",
                                     "params": {"applies_to_forms": [URBAN],
                                                "max_ft": 40}},
                         "NOT-A-RULE": {"evaluator": "mu_max_height",
                                        "params": {}}}}
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.json")
            json.dump(doc, open(p, "w"))
            with self.assertRaises(KeyError):
                RuleGraph.load(RULES_PATH, overlay_path=p)

    def test_gap_rules_still_have_no_evaluator(self):
        districts = {"MU-5-09": "MU-5", "MU-6-09": "MU-6", "MU-OPENSPACE-01": "MU-5"}
        for rid in STILL_NO_EVALUATOR:
            r = self.g.evaluate(rid, {"district": districts[rid]})
            self.assertEqual(r["outcome"], "UNKNOWN", rid)
            self.assertIn("no evaluator registered", r["reason"], rid)
            self.assertTrue(r["applicable"], rid)


class TestMuMaxHeight(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=[OVERLAY_V1, OVERLAY_V2])

    def ev(self, rid, ctx):
        return self.g.evaluate(rid, dict({"district": rid.rsplit("-", 1)[0]}, **ctx))

    def test_pass(self):
        r = self.ev("MU-5-01", {"building_form": URBAN, "height_ft": 35})
        self.assertEqual(r["outcome"], "PASS")

    def test_fail(self):
        r = self.ev("MU-5-01", {"building_form": URBAN, "height_ft": 45})
        self.assertEqual(r["outcome"], "FAIL")

    def test_unknown_height(self):
        r = self.ev("MU-5-01", {"building_form": URBAN})
        self.assertEqual(r["outcome"], "UNKNOWN")
        self.assertIn("height", r["reason"].lower())

    def test_unknown_form(self):
        r = self.ev("MU-5-01", {"height_ft": 35})
        self.assertEqual(r["outcome"], "UNKNOWN")

    def test_not_applicable_form(self):
        r = self.ev("MU-5-01", {"building_form": ROW, "height_ft": 45})
        self.assertEqual(r["outcome"], "PASS")
        self.assertIn("applies to", r["reason"])
        self.assertIn("row_house", r["reason"])

    def test_mu11_01_row_house(self):
        r = self.ev("MU-11-01", {"building_form": ROW, "height_ft": 45})
        self.assertEqual(r["outcome"], "PASS")
        r = self.ev("MU-11-01", {"building_form": ROW, "height_ft": 46})
        self.assertEqual(r["outcome"], "FAIL")


class TestMuYardRange(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=[OVERLAY_V1, OVERLAY_V2])

    def ev(self, rid, ctx):
        return self.g.evaluate(rid, dict({"district": rid.rsplit("-", 1)[0]}, **ctx))

    def test_pass(self):
        r = self.ev("MU-5-06", {"building_form": ROW,
                                "front_setback_ft": 12,
                                "corner_side_setback_ft": 15})
        self.assertEqual(r["outcome"], "PASS")

    def test_fail_below_min(self):
        r = self.ev("MU-5-06", {"building_form": ROW,
                                "front_setback_ft": 8,
                                "corner_side_setback_ft": 15})
        self.assertEqual(r["outcome"], "FAIL")

    def test_fail_above_max(self):
        r = self.ev("MU-5-06", {"building_form": ROW,
                                "front_setback_ft": 12,
                                "corner_side_setback_ft": 25})
        self.assertEqual(r["outcome"], "FAIL")

    def test_unknown_setback(self):
        r = self.ev("MU-5-06", {"building_form": ROW,
                                "front_setback_ft": 12})
        self.assertEqual(r["outcome"], "UNKNOWN")

    def test_ground_floor_scoping(self):
        base = {"building_form": MF, "front_setback_ft": 12,
                "corner_side_setback_ft": 15}
        r = self.ev("MU-5-11", dict(base, ground_floor_use="residential"))
        self.assertEqual(r["outcome"], "PASS")
        r = self.ev("MU-5-11", dict(base, ground_floor_use="non-residential"))
        self.assertEqual(r["outcome"], "PASS")
        self.assertIn("non-residential", r["reason"])
        r = self.ev("MU-5-11", dict(base))
        self.assertEqual(r["outcome"], "UNKNOWN")


class TestMuYardMinAbutment(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=[OVERLAY_V1, OVERLAY_V2])

    def ev(self, rid, ctx):
        return self.g.evaluate(rid, dict({"district": rid.rsplit("-", 1)[0]}, **ctx))

    def test_rear_pass_no_abutment(self):
        r = self.ev("MU-5-04", {"building_form": URBAN, "rear_setback_ft": 12,
                                "abuts_zones_rear": []})
        self.assertEqual(r["outcome"], "PASS")

    def test_rear_fail_base_min(self):
        # Below the unconditional base minimum -> FAIL even with abutment unknown.
        r = self.ev("MU-5-04", {"building_form": URBAN, "rear_setback_ft": 8})
        self.assertEqual(r["outcome"], "FAIL")

    def test_rear_fail_abutment(self):
        r = self.ev("MU-5-04", {"building_form": URBAN, "rear_setback_ft": 15,
                                "abuts_zones_rear": ["R-2"]})
        self.assertEqual(r["outcome"], "FAIL")

    def test_rear_pass_abutment_satisfied(self):
        r = self.ev("MU-5-04", {"building_form": URBAN, "rear_setback_ft": 22,
                                "abuts_zones_rear": ["R-2"]})
        self.assertEqual(r["outcome"], "PASS")

    def test_rear_unknown_abutment(self):
        r = self.ev("MU-5-04", {"building_form": URBAN, "rear_setback_ft": 15})
        self.assertEqual(r["outcome"], "UNKNOWN")
        self.assertIn("abutment", r["reason"].lower())

    def test_interior_flat_min(self):
        r = self.ev("MU-11-03", {"building_form": ROW,
                                 "interior_side_setback_ft": 4})
        self.assertEqual(r["outcome"], "PASS")
        r = self.ev("MU-11-03", {"building_form": ROW,
                                 "interior_side_setback_ft": 3})
        self.assertEqual(r["outcome"], "FAIL")

    def test_none_base_min_is_no_minimum_not_zero(self):
        # MU-5-13: qualitative "None" base -> zero setback is compliant...
        r = self.ev("MU-5-13", {"building_form": MF,
                                "interior_side_setback_ft": 0,
                                "abuts_zones_side": []})
        self.assertEqual(r["outcome"], "PASS")
        # ...but the 10 ft abutment minimum still bites when it applies.
        r = self.ev("MU-5-13", {"building_form": MF,
                                "interior_side_setback_ft": 5,
                                "abuts_zones_side": ["R-1"]})
        self.assertEqual(r["outcome"], "FAIL")
        r = self.ev("MU-5-13", {"building_form": MF,
                                "interior_side_setback_ft": 5})
        self.assertEqual(r["outcome"], "UNKNOWN")

    def test_mu6_rmf35_in_abutment_list(self):
        # MU-6-13/14 include RMF-35; MU-5/MU-11 abutment lists do not.
        r = self.ev("MU-6-13", {"building_form": MF,
                                "interior_side_setback_ft": 5,
                                "abuts_zones_side": ["RMF-35"]})
        self.assertEqual(r["outcome"], "FAIL")
        r = self.ev("MU-5-13", {"building_form": MF,
                                "interior_side_setback_ft": 5,
                                "abuts_zones_side": ["RMF-35"]})
        self.assertEqual(r["outcome"], "PASS")


class TestMuStreetYard(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=[OVERLAY_V1, OVERLAY_V2])

    def ev(self, ctx):
        return self.g.evaluate("MU-11-02", dict({"district": "MU-11",
                                                 "building_form": ROW}, **ctx))

    def test_pass(self):
        r = self.ev({"front_setback_ft": 12, "front_street": "400 South",
                     "corner_side_setback_ft": 6, "corner_street": "500 East"})
        self.assertEqual(r["outcome"], "PASS")

    def test_fail_listed_street(self):
        r = self.ev({"front_setback_ft": 8, "front_street": "400 South",
                     "corner_side_setback_ft": 6, "corner_street": "500 East"})
        self.assertEqual(r["outcome"], "FAIL")

    def test_fail_max(self):
        r = self.ev({"front_setback_ft": 25, "front_street": "400 South",
                     "corner_side_setback_ft": 6, "corner_street": "500 East"})
        self.assertEqual(r["outcome"], "FAIL")

    def test_segment_limited_street(self):
        base = {"corner_side_setback_ft": 6, "corner_street": "500 East"}
        # On the listed segment -> 10 ft minimum.
        r = self.ev(dict(base, front_setback_ft=6, front_street="1700 South",
                         front_street_within_listed_segment=True))
        self.assertEqual(r["outcome"], "FAIL")
        # Outside the listed segment -> base 5 ft.
        r = self.ev(dict(base, front_setback_ft=6, front_street="1700 South",
                         front_street_within_listed_segment=False))
        self.assertEqual(r["outcome"], "PASS")
        # Segment unknown -> honest UNKNOWN.
        r = self.ev(dict(base, front_setback_ft=6, front_street="1700 South"))
        self.assertEqual(r["outcome"], "UNKNOWN")

    def test_unknown_street_with_small_setback(self):
        r = self.ev({"front_setback_ft": 6,
                     "corner_side_setback_ft": 6, "corner_street": "500 East"})
        self.assertEqual(r["outcome"], "UNKNOWN")


class TestMuStreetYardMinmax(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=[OVERLAY_V1, OVERLAY_V2])

    def ev(self, ctx):
        return self.g.evaluate("MU-5-12", dict({"district": "MU-5",
                                                "building_form": MF}, **ctx))

    def test_ground_floor_scoping(self):
        base = {"front_setback_ft": 12, "front_street": "400 South",
                "corner_side_setback_ft": 12, "corner_street": "400 South"}
        r = self.ev(dict(base, ground_floor_use="non-residential"))
        self.assertEqual(r["outcome"], "PASS")
        r = self.ev(dict(base, ground_floor_use="residential"))
        self.assertEqual(r["outcome"], "PASS")
        self.assertIn("residential", r["reason"])
        r = self.ev(dict(base))
        self.assertEqual(r["outcome"], "UNKNOWN")

    def test_400_south(self):
        base = {"ground_floor_use": "non-residential",
                "corner_side_setback_ft": 12, "corner_street": "400 South"}
        r = self.ev(dict(base, front_setback_ft=12, front_street="400 South"))
        self.assertEqual(r["outcome"], "PASS")
        r = self.ev(dict(base, front_setback_ft=8, front_street="400 South"))
        self.assertEqual(r["outcome"], "FAIL")

    def test_north_temple(self):
        base = {"ground_floor_use": "non-residential",
                "corner_side_setback_ft": 12, "corner_street": "North Temple"}
        r = self.ev(dict(base, front_setback_ft=12, front_street="North Temple"))
        self.assertEqual(r["outcome"], "PASS")
        r = self.ev(dict(base, front_setback_ft=18, front_street="North Temple"))
        self.assertEqual(r["outcome"], "FAIL")

    def test_other_street_default_range(self):
        # Qualitative "None" base minimum -> default 0; 10 ft max still applies.
        base = {"ground_floor_use": "non-residential",
                "corner_side_setback_ft": 5, "corner_street": "500 East"}
        r = self.ev(dict(base, front_setback_ft=5, front_street="500 East"))
        self.assertEqual(r["outcome"], "PASS")
        r = self.ev(dict(base, front_setback_ft=12, front_street="500 East"))
        self.assertEqual(r["outcome"], "FAIL")


class TestMuBuildingFormSeparation(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH, overlay_path=[OVERLAY_V1, OVERLAY_V2])

    def ev(self, ctx):
        return self.g.evaluate("MU-5-15", dict({"district": "MU-5"}, **ctx))

    def test_unknown_forms(self):
        r = self.ev({})
        self.assertEqual(r["outcome"], "UNKNOWN")

    def test_single_form_pass(self):
        r = self.ev({"building_forms": [MF]})
        self.assertEqual(r["outcome"], "PASS")

    def test_multiple_forms_honest_unknown(self):
        r = self.ev({"building_forms": [MF, ROW]})
        self.assertEqual(r["outcome"], "UNKNOWN")
        self.assertIn("separation", r["reason"].lower())


if __name__ == "__main__":
    unittest.main()
