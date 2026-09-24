"""RuleGraph v1 tests: the gate, three-valued logic, and tamper-evidence.

Run: venv/bin/python -m unittest rulegraph.test_rulegraph -v
"""
import copy
import json
import unittest

from .engine import RuleGraph
from .fingerprint import canonical_hash

# Pinned fingerprint of verified_rules.json (canonical 59-rule store,
# 2026-09-24 integration). ANY edit to the rule store changes this — update
# the pin deliberately when a human re-verifies and the store legitimately
# changes.
# SUPERSEDED: 664ac3541b0bc9b8b8c5130ec6912367f9b1e03a7f08b58d714d80c5ed7dc0fe
# was the 10-rule store pin (archived at
# rulegraph/verified_rules.v1_10rule.json).
PINNED_FINGERPRINT = "9cc91ac71f5f1de221b9609291ce264ca33d6c6ba9b98f7e7f898778fd0cfd1c"

RULES_PATH = "rulegraph/verified_rules.json"


def compliant_context():
    return {
        "district": "MU-11",
        "lot_abuts_sf_tf_residential": False,
        "landscape_buffer_provided": None,
        "building_form": "row_house",
        "stories": [
            {"level": 0, "use": "live_work"},
            {"level": 1, "use": "residential"},
            {"level": 2, "use": "residential"},
        ],
        "height_ft": 80,
        "design_review_completed": None,
        "in_height_bonus_area": None,
        "open_space_ground_pct": None,
        "enhanced_active_use_100_pct": None,
        "midblock_walkway_ft": None,
        "front_setback_ft": 12,
        "front_street": "Main Street",
        "front_street_within_listed_segment": None,
        "corner_side_setback_ft": 12,
        "corner_street": "Main Street",
        "corner_street_within_listed_segment": None,
        "interior_side_setback_ft": 5,
        "interior_abuts_listed_zone": False,
        "rear_setback_ft": 5,
        "rear_abuts_listed_zone": False,
    }


class TestGate(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH)

    def test_all_59_rules_load(self):
        self.assertEqual(len(self.g.rules), 59)

    def test_unverified_rule_never_executes(self):
        # The gate reads human_verification, not the legacy top-level status:
        # even with status left "VERIFIED", a UNVERIFIED human result must not execute.
        rules = RuleGraph.load(RULES_PATH).rules
        r = copy.deepcopy(rules["MU-11-06"])
        r["rule_id"] = "MU-11-99"
        r["human_verification"]["result"] = "UNVERIFIED"
        g2 = RuleGraph([r])
        res = g2.evaluate("MU-11-99", {"height_ft": 9999})
        self.assertEqual(res["outcome"], "UNKNOWN")

    def test_rejected_rule_never_executes(self):
        rules = RuleGraph.load(RULES_PATH).rules
        r = copy.deepcopy(rules["MU-11-06"])
        r["rule_id"] = "MU-11-98"
        r["human_verification"]["result"] = "REJECTED"
        g2 = RuleGraph([r])
        res = g2.evaluate("MU-11-98", {"height_ft": 10})
        self.assertEqual(res["outcome"], "UNKNOWN")

    # --- stale top-level "status" can never authorize execution ---
    # A human verdict is valid only with result + verifier identity + date.

    def _rule_with(self, **hv_overrides):
        rules = RuleGraph.load(RULES_PATH).rules
        r = copy.deepcopy(rules["MU-11-06"])
        r["rule_id"] = "MU-11-9X"
        r["status"] = "VERIFIED"  # stale legacy label; must be ignored by the gate
        for k, v in hv_overrides.items():
            if v is None:
                r["human_verification"].pop(k, None)
            else:
                r["human_verification"][k] = v
        return r

    def test_status_verified_but_human_verification_missing_is_unknown(self):
        # (a) top-level status VERIFIED, no human_verification record at all
        r = self._rule_with()
        del r["human_verification"]
        g2 = RuleGraph([r])
        res = g2.evaluate("MU-11-9X", {"height_ft": 10})
        self.assertEqual(res["outcome"], "UNKNOWN")

    def test_status_verified_but_result_pending_is_unknown(self):
        # (b) top-level status VERIFIED, human result is PENDING/DRAFT-ish
        for result in ("PENDING", "DRAFT", "UNVERIFIED", None, ""):
            r = self._rule_with(result=result)
            g2 = RuleGraph([r])
            res = g2.evaluate("MU-11-9X", {"height_ft": 10})
            self.assertEqual(res["outcome"], "UNKNOWN", f"result={result!r}")

    def test_result_verified_but_verified_by_empty_is_unknown(self):
        # (c) verdict present but no verifier identity
        for by in ("", "   ", None):
            r = self._rule_with(result="VERIFIED", verified_by=by)
            g2 = RuleGraph([r])
            res = g2.evaluate("MU-11-9X", {"height_ft": 10})
            self.assertEqual(res["outcome"], "UNKNOWN", f"verified_by={by!r}")

    def test_result_verified_but_verified_on_empty_is_unknown(self):
        # (d) verdict present but no verification date
        for on in ("", "   ", None):
            r = self._rule_with(result="VERIFIED", verified_on=on)
            g2 = RuleGraph([r])
            res = g2.evaluate("MU-11-9X", {"height_ft": 10})
            self.assertEqual(res["outcome"], "UNKNOWN", f"verified_on={on!r}")

    def test_corrected_executes_like_verified(self):
        # (e) CORRECTED authorizes execution exactly like VERIFIED
        r = self._rule_with(result="CORRECTED")
        g2 = RuleGraph([r])
        res = g2.evaluate("MU-11-9X", compliant_context())
        self.assertEqual(res["outcome"], "PASS")
        res = g2.evaluate("MU-11-9X", {**compliant_context(), "height_ft": 9999})
        self.assertEqual(res["outcome"], "FAIL")  # it genuinely executes, not a blanket PASS

    def test_stale_status_alone_never_executes_even_when_compliant(self):
        # Belt and suspenders: legacy status VERIFIED + compliant context,
        # but result missing -> UNKNOWN (never a silent PASS).
        r = self._rule_with(result=None)
        g2 = RuleGraph([r])
        res = g2.evaluate("MU-11-9X", compliant_context())
        self.assertEqual(res["outcome"], "UNKNOWN")

    def test_unknown_rule_id_raises_loud(self):
        with self.assertRaises(KeyError):
            self.g.evaluate("NOPE-01", {})

    def test_fingerprint_pinned(self):
        self.assertEqual(self.g.fingerprint, PINNED_FINGERPRINT)

    def test_tamper_changes_fingerprint(self):
        rules = list(RuleGraph.load(RULES_PATH).rules.values())
        tampered = copy.deepcopy(rules)
        tampered[0]["params"] = {"injected": True}
        h1 = canonical_hash({"rules": rules})
        h2 = canonical_hash({"rules": tampered})
        self.assertNotEqual(h1, h2)


class TestDistrictScoping(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH)

    def test_matching_district_evaluates(self):
        ctx = compliant_context()  # district MU-11
        res = self.g.evaluate("MU-11-06", ctx)
        self.assertTrue(res["applicable"])
        self.assertEqual(res["outcome"], "PASS")

    def test_mismatched_district_not_applicable(self):
        ctx = compliant_context()
        ctx["district"] = "R-1-8"
        ctx["height_ft"] = 999  # would FAIL if evaluated
        res = self.g.evaluate("MU-11-06", ctx)
        self.assertFalse(res["applicable"])
        self.assertEqual(res["outcome"], "PASS")

    def test_unknown_district_evaluates_normally(self):
        ctx = compliant_context()
        ctx["district"] = None
        ctx["height_ft"] = 999
        res = self.g.evaluate("MU-11-06", ctx)
        self.assertTrue(res["applicable"])
        self.assertEqual(res["outcome"], "FAIL")

    def test_pl04_scoped_out_on_mu11_parcel(self):
        ctx = compliant_context()  # district MU-11
        ctx.update(lot_abuts_sf_tf_residential=True, landscape_buffer_provided=False)
        res = self.g.evaluate("PL-04", ctx)
        self.assertFalse(res["applicable"])
        self.assertEqual(res["outcome"], "PASS")

    def test_gate_beats_district_scope(self):
        # Unverified + wrong district -> still UNKNOWN (gate is conservative)
        rules = RuleGraph.load(RULES_PATH).rules
        r = copy.deepcopy(rules["MU-11-06"])
        r["rule_id"] = "MU-11-97"
        r["human_verification"]["result"] = "UNVERIFIED"
        g2 = RuleGraph([r])
        ctx = compliant_context()
        ctx["district"] = "R-1-8"
        res = g2.evaluate("MU-11-97", ctx)
        self.assertEqual(res["outcome"], "UNKNOWN")


class TestAbsenceRules(unittest.TestCase):
    """MU-5-16, MU-6-16 (recorded from the 59/59 human-verified milestone) and
    MU-11-11 (broadened by the 2026-09-23 22:43 code-wide sweep): unqualified
    'no minimum lot area or width' for their districts."""

    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH)

    def test_mu5_16_passes_on_mu5(self):
        res = self.g.evaluate("MU-5-16", {"district": "MU-5"})
        self.assertTrue(res["applicable"])
        self.assertEqual(res["outcome"], "PASS")
        self.assertEqual(res["status"], "VERIFIED")
        self.assertIn("code-wide human-verified sweep", res["reason"])

    def test_mu6_16_passes_on_mu6(self):
        res = self.g.evaluate("MU-6-16", {"district": "MU-6"})
        self.assertTrue(res["applicable"])
        self.assertEqual(res["outcome"], "PASS")
        self.assertEqual(res["status"], "VERIFIED")

    def test_mu11_11_broadened_passes_on_mu11(self):
        res = self.g.evaluate("MU-11-11", {"district": "MU-11"})
        self.assertTrue(res["applicable"])
        self.assertEqual(res["outcome"], "PASS")
        self.assertEqual(res["status"], "VERIFIED")
        self.assertIn("MU-11 Mixed Use 11 District", res["reason"])

    def test_absence_rules_scoped_out_on_other_districts(self):
        res = self.g.evaluate("MU-5-16", {"district": "MU-11"})
        self.assertFalse(res["applicable"])
        self.assertEqual(res["outcome"], "PASS")
        res = self.g.evaluate("MU-11-11", {"district": "MU-5"})
        self.assertFalse(res["applicable"])
        self.assertEqual(res["outcome"], "PASS")

    def test_absence_rules_carry_human_verdicts(self):
        rules = self.g.rules
        for rid, by in (("MU-5-16", "Rohan"), ("MU-6-16", "Rohan"),
                        ("MU-11-11", "Rishab")):
            hv = rules[rid]["human_verification"]
            self.assertEqual(hv["result"], "VERIFIED", rid)
            self.assertEqual(hv["verified_by"], by, rid)
            self.assertEqual(hv["verified_on"], "2026-09-23", rid)

    def test_broadened_by_sweep_provenance_quotes_sweep_verbatim(self):
        rules = self.g.rules
        for rid in ("MU-5-16", "MU-6-16", "MU-11-11"):
            prov = rules[rid]["broadened_by_sweep"]
            self.assertIn("SWEEP RESULT", prov["sweep_quote"], rid)
            self.assertIn("no minimum' without qualification", prov["sweep_quote"], rid)

    def test_no_pending_title20_qualifier_remains(self):
        # The narrow-era "Title 20 check pending" qualifier must be gone from
        # every absence rule: the sweep resolved the Title 20 leg.
        for rid in ("MU-5-16", "MU-6-16", "MU-11-11"):
            rule = self.g.rules[rid]
            blob = json.dumps(rule)
            self.assertNotIn("pending", blob.lower(), rid)


class TestAdapter(unittest.TestCase):
    def test_no_program_all_unknown(self):
        from . import adapter as rg_adapter
        ctx, prov = rg_adapter.build_context(zoning_cfg={})
        g = RuleGraph.load(RULES_PATH)
        verdict = g.scheme_verdict(ctx)
        self.assertEqual(verdict["verdict"], "UNKNOWN")
        gaps = rg_adapter.summarize_gaps([prov])
        self.assertTrue(len(gaps) > 10)  # nearly everything is a gap without a program

    def test_program_typo_raises(self):
        from . import adapter as rg_adapter
        with self.assertRaises(ValueError):
            rg_adapter.build_context(program={"height_ftt": 40})

    def test_underscore_keys_ignored(self):
        from . import adapter as rg_adapter
        ctx, _ = rg_adapter.build_context(program={"_note": "hi", "height_ft": 40})
        self.assertEqual(ctx["height_ft"], 40)

    def test_zoning_district_flows_through(self):
        from . import adapter as rg_adapter
        ctx, prov = rg_adapter.build_context(zoning_cfg={"district": "MU-11"})
        self.assertEqual(ctx["district"], "MU-11")
        self.assertEqual(prov["district"][0], "known")

    def test_program_district_overrides_zoning(self):
        from . import adapter as rg_adapter
        ctx, _ = rg_adapter.build_context(
            zoning_cfg={"district": "R-1-8"}, program={"district": "MU-11"})
        self.assertEqual(ctx["district"], "MU-11")


class TestCornerLotContract(unittest.TestCase):
    """is_corner_lot: contract readiness. No current rule consumes it."""

    def test_contract_has_24_attributes(self):
        from . import adapter as rg_adapter
        # 24 original + 8 Caddy-extraction-v1 attributes (M-1/OS/PL facts)
        # + 2 Caddy-extraction-v2 attributes (MU facts).
        self.assertEqual(len(rg_adapter.CONTRACT_ATTRS), 34)
        self.assertIn("is_corner_lot", rg_adapter.CONTRACT_ATTRS)
        self.assertIn("abuts_zones_side", rg_adapter.CONTRACT_ATTRS)
        self.assertIn("abuts_zones_rear", rg_adapter.CONTRACT_ATTRS)
        self.assertIn("proposed_use_is_public_school", rg_adapter.CONTRACT_ATTRS)
        self.assertIn("in_m1_height_exception_zone", rg_adapter.CONTRACT_ATTRS)
        self.assertIn("building_forms", rg_adapter.CONTRACT_ATTRS)
        self.assertIn("ground_floor_use", rg_adapter.CONTRACT_ATTRS)

    def test_corner_lot_true_flows_through(self):
        from . import adapter as rg_adapter
        ctx, prov = rg_adapter.build_context(program={"is_corner_lot": True})
        self.assertIs(ctx["is_corner_lot"], True)
        self.assertEqual(prov["is_corner_lot"], ("known", "building program"))

    def test_corner_lot_false_flows_through(self):
        from . import adapter as rg_adapter
        ctx, prov = rg_adapter.build_context(program={"is_corner_lot": False})
        self.assertIs(ctx["is_corner_lot"], False)
        self.assertEqual(prov["is_corner_lot"][0], "known")

    def test_corner_lot_absent_is_unknown_with_gap_note(self):
        from . import adapter as rg_adapter
        ctx, prov = rg_adapter.build_context(zoning_cfg={})
        self.assertIsNone(ctx["is_corner_lot"])
        self.assertEqual(prov["is_corner_lot"][0], "unknown")
        self.assertEqual(prov["is_corner_lot"][1], rg_adapter.GAP_NOTES["is_corner_lot"])
        gaps = rg_adapter.summarize_gaps([prov])
        attrs = [g["attribute"] for g in gaps]
        self.assertIn("is_corner_lot", attrs)

    def test_corner_lot_does_not_change_verdicts(self):
        # No rule consumes is_corner_lot yet; verdicts must be identical
        # whether or not the attribute is present.
        from . import adapter as rg_adapter
        g = RuleGraph.load(RULES_PATH)
        base = {k: v for k, v in compliant_context().items() if k != "district"}
        ctx_without, _ = rg_adapter.build_context(
            zoning_cfg={"district": "MU-11"}, program=base)
        ctx_with, _ = rg_adapter.build_context(
            zoning_cfg={"district": "MU-11"},
            program={**base, "is_corner_lot": True},
        )
        v_without = g.scheme_verdict(ctx_without)
        v_with = g.scheme_verdict(ctx_with)
        self.assertEqual(v_with["verdict"], v_without["verdict"])
        self.assertEqual(
            [r["outcome"] for r in v_with["results"]],
            [r["outcome"] for r in v_without["results"]],
        )


class TestAbutmentZones(unittest.TestCase):
    """abuts_zones_side / abuts_zones_rear: zone-code lists for MU-11-09/10.

    Listed zone present -> the abutment minimum applies. Unlisted zones only
    (or an empty, i.e. surveyed, list) -> base case, no minimum. Absent list
    and absent boolean -> UNKNOWN. A present list takes precedence over the
    legacy boolean; a malformed list is UNKNOWN, never evidence.
    """

    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH)

    def _ctx(self, **overrides):
        ctx = compliant_context()
        # Strip the legacy booleans so the list path is exercised on its own.
        ctx["interior_abuts_listed_zone"] = None
        ctx["rear_abuts_listed_zone"] = None
        ctx.update(overrides)
        return ctx

    def _eval_outcome(self, rule_id, **overrides):
        res = self.g.evaluate(rule_id, self._ctx(**overrides))
        return res["outcome"], res["reason"]

    # --- MU-11-09 (interior side, 10 ft when abutting) ---

    def test_listed_zone_in_list_applies_minimum(self):
        oc, reason = self._eval_outcome("MU-11-09", interior_side_setback_ft=5,
                                   abuts_zones_side=["R-1"])
        self.assertEqual(oc, "FAIL", reason)
        self.assertIn("R-1", reason)

    def test_multiple_zones_one_listed(self):
        oc, reason = self._eval_outcome("MU-11-09", interior_side_setback_ft=5,
                                   abuts_zones_side=["MU-11", "RMF-35", "MU-2"])
        self.assertEqual(oc, "FAIL", reason)

    def test_unlisted_zone_only_no_minimum(self):
        oc, reason = self._eval_outcome("MU-11-09", interior_side_setback_ft=5,
                                   abuts_zones_side=["MU-11"])
        self.assertEqual(oc, "PASS", reason)

    def test_empty_list_means_surveyed_no_abutment(self):
        oc, reason = self._eval_outcome("MU-11-09", interior_side_setback_ft=5,
                                   abuts_zones_side=[])
        self.assertEqual(oc, "PASS", reason)

    def test_absent_list_and_bool_is_unknown(self):
        oc, _ = self._eval_outcome("MU-11-09", interior_side_setback_ft=5)
        self.assertEqual(oc, "UNKNOWN")

    def test_list_takes_precedence_over_bool(self):
        # List says R-1 abuts, legacy bool says no -> the list wins -> FAIL.
        oc, _ = self._eval_outcome("MU-11-09", interior_side_setback_ft=5,
                              abuts_zones_side=["R-1"],
                              interior_abuts_listed_zone=False)
        self.assertEqual(oc, "FAIL")
        # Empty (surveyed) list beats a True legacy bool -> PASS.
        oc, _ = self._eval_outcome("MU-11-09", interior_side_setback_ft=5,
                              abuts_zones_side=[],
                              interior_abuts_listed_zone=True)
        self.assertEqual(oc, "PASS")

    def test_malformed_list_is_unknown(self):
        oc, reason = self._eval_outcome("MU-11-09", interior_side_setback_ft=5,
                                   abuts_zones_side="R-1")
        self.assertEqual(oc, "UNKNOWN", reason)

    def test_high_setback_passes_with_listed_abutment(self):
        oc, _ = self._eval_outcome("MU-11-09", interior_side_setback_ft=12,
                              abuts_zones_side=["R-1"])
        self.assertEqual(oc, "PASS")

    def test_bool_fallback_still_works_without_list(self):
        oc, _ = self._eval_outcome("MU-11-09", interior_side_setback_ft=5,
                              interior_abuts_listed_zone=True)
        self.assertEqual(oc, "FAIL")
        oc, _ = self._eval_outcome("MU-11-09", interior_side_setback_ft=5,
                              interior_abuts_listed_zone=False)
        self.assertEqual(oc, "PASS")

    # --- MU-11-10 (rear, 20 ft when abutting) ---

    def test_rear_listed_zone_applies_minimum(self):
        oc, reason = self._eval_outcome("MU-11-10", rear_setback_ft=10,
                                   abuts_zones_rear=["RMF-30"])
        self.assertEqual(oc, "FAIL", reason)

    def test_rear_unlisted_zone_no_minimum(self):
        oc, _ = self._eval_outcome("MU-11-10", rear_setback_ft=10,
                              abuts_zones_rear=["MU-11"])
        self.assertEqual(oc, "PASS")

    def test_rear_absent_is_unknown(self):
        oc, _ = self._eval_outcome("MU-11-10", rear_setback_ft=10)
        self.assertEqual(oc, "UNKNOWN")

    # --- adapter wiring: lists flow from the program with provenance ---

    def test_zone_lists_flow_through_adapter(self):
        from . import adapter as rg_adapter
        ctx, prov = rg_adapter.build_context(
            zoning_cfg={"district": "MU-11"},
            program={"abuts_zones_side": ["R-1"], "abuts_zones_rear": []},
        )
        self.assertEqual(ctx["abuts_zones_side"], ["R-1"])
        self.assertEqual(ctx["abuts_zones_rear"], [])
        self.assertEqual(prov["abuts_zones_side"], ("known", "building program"))
        self.assertEqual(prov["abuts_zones_rear"], ("known", "building program"))

    def test_zone_lists_change_verdicts_end_to_end(self):
        from . import adapter as rg_adapter
        g = RuleGraph.load(RULES_PATH)
        base = {k: v for k, v in compliant_context().items()
                if k not in ("interior_abuts_listed_zone", "rear_abuts_listed_zone")}
        ctx, _ = rg_adapter.build_context(
            zoning_cfg={"district": "MU-11"},
            program={**base, "abuts_zones_side": ["R-1"], "abuts_zones_rear": []},
        )
        verdict = g.scheme_verdict(ctx)
        by_id = {r["rule_id"]: r for r in verdict["results"]}
        self.assertEqual(by_id["MU-11-09"]["outcome"], "FAIL")
        self.assertEqual(by_id["MU-11-10"]["outcome"], "PASS")
        self.assertEqual(verdict["verdict"], "FAIL")


class TestCompliantScheme(unittest.TestCase):
    def test_compliant_context_honest_unknowns(self):
        # Canonical 59-rule store: the 7 executable MU-11 rules PASS on the
        # compliant context; the 5 stored-but-not-executable MU-11 rules
        # (MU-11-01..04, MU-OPENSPACE-01) yield UNKNOWN — verified rules the
        # engine cannot execute yet. Aggregation: UNKNOWN outranks PASS.
        g = RuleGraph.load(RULES_PATH)
        verdict = g.scheme_verdict(compliant_context())
        self.assertEqual(verdict["verdict"], "UNKNOWN")
        by_id = {r["rule_id"]: r for r in verdict["results"]}
        for rid in ("MU-11-05", "MU-11-06", "MU-11-07", "MU-11-08",
                    "MU-11-09", "MU-11-10", "MU-11-11"):
            self.assertEqual(by_id[rid]["outcome"], "PASS", rid)
        for rid in ("MU-11-01", "MU-11-02", "MU-11-03", "MU-11-04",
                    "MU-OPENSPACE-01"):
            self.assertEqual(by_id[rid]["outcome"], "UNKNOWN", rid)
            self.assertIn("no evaluator", by_id[rid]["reason"])


class TestFailCases(unittest.TestCase):
    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH)

    def _fails(self, rule_id, **overrides):
        ctx = compliant_context()
        ctx.update(overrides)
        res = self.g.evaluate(rule_id, ctx)
        self.assertEqual(res["outcome"], "FAIL", f"{rule_id}: {res['reason']}")
        return res

    def test_pl04_no_buffer(self):
        self._fails("PL-04", district="PL", lot_abuts_sf_tf_residential=True, landscape_buffer_provided=False)

    def test_mu1105_commercial_upper_story(self):
        self._fails("MU-11-05", stories=[
            {"level": 0, "use": "live_work"}, {"level": 1, "use": "commercial"}])

    def test_mu1105_live_work_upper_story(self):
        self._fails("MU-11-05", stories=[
            {"level": 0, "use": "residential"}, {"level": 1, "use": "live_work"}])

    def test_mu1106_over_max(self):
        self._fails("MU-11-06", height_ft=130, in_height_bonus_area=False)

    def test_mu1106_over_base_but_bonus_satisfied(self):
        ctx = compliant_context()
        ctx.update(height_ft=140, in_height_bonus_area=True,
                   design_review_completed=True, open_space_ground_pct=12,
                   enhanced_active_use_100_pct=True)
        res = self.g.evaluate("MU-11-06", ctx)
        self.assertEqual(res["outcome"], "PASS", f"MU-11-06: {res['reason']}")

    def test_mu1106_over_base_bonus_unknown(self):
        ctx = compliant_context()
        ctx.update(height_ft=140, in_height_bonus_area=None)
        res = self.g.evaluate("MU-11-06", ctx)
        self.assertEqual(res["outcome"], "UNKNOWN", f"MU-11-06: {res['reason']}")

    def test_mu1106_no_design_review(self):
        self._fails("MU-11-06", height_ft=100, design_review_completed=False)

    def test_mu1107_over_bonus_max(self):
        self._fails("MU-11-07", height_ft=160)

    def test_mu1107_outside_bonus_area(self):
        self._fails("MU-11-07", height_ft=140, in_height_bonus_area=False)

    def test_mu1107_missing_walkway_and_active_use(self):
        self._fails("MU-11-07", height_ft=140, in_height_bonus_area=True,
                    design_review_completed=True, open_space_ground_pct=12,
                    enhanced_active_use_100_pct=False, midblock_walkway_ft=10)

    def test_mu1107_open_space_short(self):
        self._fails("MU-11-07", height_ft=140, in_height_bonus_area=True,
                    design_review_completed=True, open_space_ground_pct=5,
                    enhanced_active_use_100_pct=True)

    def test_mu1108_over_max_setback(self):
        self._fails("MU-11-08", front_setback_ft=25)

    def test_mu1108_north_temple_short(self):
        self._fails("MU-11-08", front_street="North Temple", front_setback_ft=3)

    def test_mu1108_listed_street_short(self):
        self._fails("MU-11-08", front_street="400 South", front_setback_ft=7)

    def test_mu1109_abutment_short(self):
        self._fails("MU-11-09", interior_side_setback_ft=5, interior_abuts_listed_zone=True)

    def test_mu1110_abutment_short(self):
        self._fails("MU-11-10", rear_setback_ft=10, rear_abuts_listed_zone=True)

    def test_scheme_verdict_fail(self):
        ctx = compliant_context()
        ctx["height_ft"] = 200
        self.assertEqual(self.g.scheme_verdict(ctx)["verdict"], "FAIL")


class TestUnknownCases(unittest.TestCase):
    """Missing info must NEVER silently become PASS."""

    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH)

    def _unknown(self, rule_id, **overrides):
        ctx = compliant_context()
        ctx.update(overrides)
        res = self.g.evaluate(rule_id, ctx)
        self.assertEqual(res["outcome"], "UNKNOWN", f"{rule_id}: {res['reason']}")
        return res

    def test_pl04_abutment_unknown(self):
        self._unknown("PL-04", district="PL", lot_abuts_sf_tf_residential=None)

    def test_pl04_buffer_status_unknown(self):
        self._unknown("PL-04", district="PL", lot_abuts_sf_tf_residential=True, landscape_buffer_provided=None)

    def test_mu1105_stories_unknown(self):
        self._unknown("MU-11-05", stories=None)

    def test_mu1105_form_unknown(self):
        self._unknown("MU-11-05", building_form=None)

    def test_mu1106_height_unknown(self):
        self._unknown("MU-11-06", height_ft=None)

    def test_mu1106_design_review_unknown(self):
        self._unknown("MU-11-06", height_ft=100, design_review_completed=None)

    def test_mu1107_bonus_area_unknown(self):
        self._unknown("MU-11-07", height_ft=140, in_height_bonus_area=None)

    def test_mu1108_street_unknown_low_setback(self):
        self._unknown("MU-11-08", front_street=None, front_setback_ft=3)

    def test_mu1108_segment_unknown_low_setback(self):
        self._unknown("MU-11-08", front_street="1700 South",
                      front_street_within_listed_segment=None, front_setback_ft=7)

    def test_mu1109_abutment_unknown(self):
        self._unknown("MU-11-09", interior_side_setback_ft=5, interior_abuts_listed_zone=None)

    def test_mu1110_abutment_unknown(self):
        self._unknown("MU-11-10", rear_setback_ft=10, rear_abuts_listed_zone=None)

    def test_scheme_verdict_unknown(self):
        ctx = compliant_context()
        ctx["height_ft"] = None  # MU-11-06/07 go UNKNOWN, everything else PASS
        self.assertEqual(self.g.scheme_verdict(ctx)["verdict"], "UNKNOWN")


class TestHonestPassEdges(unittest.TestCase):
    """Cases that look risky but are genuinely PASS — pinned so they stay honest."""

    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH)

    def _passes(self, rule_id, **overrides):
        ctx = compliant_context()
        ctx.update(overrides)
        res = self.g.evaluate(rule_id, ctx)
        self.assertEqual(res["outcome"], "PASS", f"{rule_id}: {res['reason']}")

    def test_mu1106_tall_with_design_review(self):
        self._passes("MU-11-06", height_ft=120, design_review_completed=True)

    def test_mu1107_bonus_with_walkway(self):
        self._passes("MU-11-07", height_ft=150, in_height_bonus_area=True,
                     design_review_completed=True, open_space_ground_pct=10,
                     enhanced_active_use_100_pct=False, midblock_walkway_ft=20)

    def test_mu1108_high_setback_unknown_street(self):
        # 12 ft satisfies every possible minimum in the rule -> genuinely PASS
        self._passes("MU-11-08", front_street=None, front_setback_ft=12)

    def test_mu1108_segment_outside_listed(self):
        self._passes("MU-11-08", front_street="1700 South",
                     front_street_within_listed_segment=False, front_setback_ft=3)

    def test_mu1109_high_setback_abutment_unknown(self):
        # 12 ft >= 10 ft abutment minimum regardless of abutment -> genuinely PASS
        self._passes("MU-11-09", interior_side_setback_ft=12, interior_abuts_listed_zone=None)

    def test_mu1105_non_row_house_not_applicable(self):
        self._passes("MU-11-05", building_form="multifamily", stories=None)


class TestCanonicalIntegration(unittest.TestCase):
    """2026-09-24 canonical 59-rule integration: multi-district scoping, the
    new M-1-02 flat-yards predicate, OS-01 absence handling, and honest
    UNKNOWN for stored-but-not-executable rules."""

    def setUp(self):
        self.g = RuleGraph.load(RULES_PATH)

    def test_multi_district_rule_applies_to_each_member(self):
        # MU-OPENSPACE-01 is stored (Rohan-VERIFIED, 10% of lot area) but not
        # executable; scoping must still recognize all three member districts.
        for district in ("MU-5", "MU-6", "MU-11"):
            ctx = {"district": district}
            res = self.g.evaluate("MU-OPENSPACE-01", ctx)
            self.assertTrue(
                res["applicable"], f"MU-OPENSPACE-01 should apply to {district}"
            )
            self.assertEqual(res["outcome"], "UNKNOWN")  # no evaluator

    def test_multi_district_rule_outside_members(self):
        ctx = {"district": "M-1"}
        res = self.g.evaluate("MU-OPENSPACE-01", ctx)
        self.assertFalse(res["applicable"])
        self.assertEqual(res["outcome"], "PASS")

    def test_engine_alias_resolves_to_canonical(self):
        # Agent-agreed alias (LeBron 2026-09-24 01:13, cross-team contract):
        # MU-OPEN-01 resolves to MU-OPENSPACE-01; MU-OS-01 is a deprecated
        # fallback from the 01:11/01:13 wording slip and resolves identically.
        # The canonical rule_id is what the store reports.
        for rid in ("MU-OPENSPACE-01", "MU-OPEN-01", "MU-OS-01"):
            res = self.g.evaluate(rid, {"district": "MU-5"})
            self.assertEqual(res["rule_id"], "MU-OPENSPACE-01")
            self.assertTrue(res["applicable"])

    def test_m102_flat_minima_pass(self):
        ctx = {
            "district": "M-1",
            "front_setback_ft": 15,
            "corner_side_setback_ft": 20,
            "interior_side_setback_ft": 0,
            "rear_setback_ft": 5,
        }
        res = self.g.evaluate("M-1-02", ctx)
        self.assertTrue(res["applicable"])
        self.assertEqual(res["outcome"], "PASS")

    def test_m102_front_below_minimum_fails(self):
        ctx = {
            "district": "M-1",
            "front_setback_ft": 10,
            "corner_side_setback_ft": 15,
            "interior_side_setback_ft": 0,
            "rear_setback_ft": 0,
        }
        res = self.g.evaluate("M-1-02", ctx)
        self.assertEqual(res["outcome"], "FAIL")

    def test_m102_unknown_yard_is_unknown(self):
        ctx = {
            "district": "M-1",
            "front_setback_ft": 15,
            "corner_side_setback_ft": None,  # unknown -> UNKNOWN, not PASS
            "interior_side_setback_ft": 0,
            "rear_setback_ft": 0,
        }
        res = self.g.evaluate("M-1-02", ctx)
        self.assertEqual(res["outcome"], "UNKNOWN")

    def test_m102_scoped_to_m1(self):
        ctx = {
            "district": "MU-11",
            "front_setback_ft": 0,  # would FAIL if evaluated
            "corner_side_setback_ft": 0,
            "interior_side_setback_ft": 0,
            "rear_setback_ft": 0,
        }
        res = self.g.evaluate("M-1-02", ctx)
        self.assertFalse(res["applicable"])
        self.assertEqual(res["outcome"], "PASS")

    def test_os01_absence_passes(self):
        ctx = {"district": "OS"}
        res = self.g.evaluate("OS-01", ctx)
        self.assertTrue(res["applicable"])
        self.assertEqual(res["outcome"], "PASS")

    def test_stored_but_not_executable_is_unknown(self):
        # M-1-01 ("None required" front, 30 side/rear w/ use-form scoping) has
        # no evaluator: VERIFIED but honest UNKNOWN, never guessed.
        res = self.g.evaluate("M-1-01", {"district": "M-1"})
        self.assertTrue(res["applicable"])
        self.assertEqual(res["outcome"], "UNKNOWN")
        self.assertIn("no evaluator", res["reason"])


if __name__ == "__main__":
    unittest.main()
