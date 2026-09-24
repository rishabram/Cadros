"""Tests for the use-allowance adapter + verdict engine.

Unit tests use small hand-built UsePack fixtures (no dependence on the real
pack file), mirroring the binding pack.py contract. One integration test
loads the real pack via load_pack() and is SKIPPED until the sibling
pack.py lands.
"""
import unittest
from dataclasses import dataclass, field

# Real pack types when the sibling module has landed; a contract-identical
# stand-in otherwise (same field names, same semantics).
try:
    from useallow.pack import UseRow, UsePack, load_pack

    PACK_AVAILABLE = True
except ImportError:  # pragma: no cover - sibling not landed yet
    PACK_AVAILABLE = False

    @dataclass
    class UseRow:
        rule_id: str
        district: str
        use_name: str
        marking: str
        status: str
        footnotes: list = field(default_factory=list)
        flags: str = ""
        provenance: str = ""
        human_verification: dict = None

    @dataclass
    class UsePack:
        rows: list
        fingerprint: str = ""

    load_pack = None

from useallow.adapter import (
    USE_ATTRS,
    build_use_context,
    program_for_scheme,
    split_program,
)
from useallow.engine import evaluate_uses

HV = {"result": "VERIFIED", "verified_by": "Rohan", "verified_on": "2026-09-23"}


_HV_DEFAULT = object()


def make_row(rule_id, district, use_name, marking, status,
             footnotes=(), flags="", provenance="live-text", hv=_HV_DEFAULT):
    return UseRow(
        rule_id=rule_id,
        district=district,
        use_name=use_name,
        marking=marking,
        status=status,
        footnotes=list(footnotes),
        flags=flags,
        provenance=provenance,
        human_verification=dict(HV) if hv is _HV_DEFAULT else hv,
    )


def fixture_pack():
    rows = [
        # M-1 U-02: permitted, footnote-free.
        make_row("M1-U-02", "M-1", "Agricultural use", "P / P / P", "permitted"),
        # M-1 U-03: conditional but footnoted -> manual review.
        make_row("M1-U-03", "M-1", "Bar establishment", "C 6,10 / C 6,10 / C 6,10",
                 "conditional", footnotes=(6, 10)),
        # M-1 U-13: conditional, footnote-free -> C.
        make_row("M1-U-13", "M-1", "Raising of furbearing animals",
                 "C / P", "conditional"),
        # M-1 U-28: unresolved (single marking, owning column unverifiable).
        make_row("M1-U-28", "M-1", "Check cashing/payday loan business",
                 "P 9 (single mark)", "unresolved",
                 flags="UNRESOLVED — single marking, owning column unverifiable from text"),
        # M-1 U-29: blank M-1 cell -> not permitted.
        make_row("M1-U-29", "M-1", "Chemical manufacturing and/or storage",
                 "C 19 (single mark)", "not_permitted",
                 flags="single marking sits in M-2 or M-3 per visual extraction"),
        # OS U-02: permitted in OS only (district scoping).
        make_row("OS-U-02", "OS", "Agricultural use", "P", "permitted"),
        # OS U-27: status ambiguous in extraction -> unresolved.
        make_row("OS-U-27", "OS", "Reception center", "P 20 / C 22",
                 "unresolved",
                 flags="STATUS AMBIGUOUS: extraction lists Permitted (P 20) in one "
                       "place and Conditional (C 22) in another"),
        # Unverified row: gate must fire.
        make_row("M1-U-XX", "M-1", "Hypothetical workshop", "P",
                 "permitted", hv=None),
        # Second row for one use, to test most-restrictive tie-break.
        make_row("M1-U-13B", "M-1", "Raising of furbearing animals",
                 "blank", "not_permitted"),
    ]
    return UsePack(rows=rows, fingerprint="fixture")


class AdapterTest(unittest.TestCase):
    def test_context_attrs(self):
        self.assertEqual(USE_ATTRS, ["district", "proposed_uses"])

    def test_build_use_context_known(self):
        ctx, prov = build_use_context(
            zoning_cfg={"district": "M-1"},
            program={"proposed_uses": ["Agricultural use"]},
        )
        self.assertEqual(ctx, {"district": "M-1",
                               "proposed_uses": ["Agricultural use"]})
        self.assertEqual(prov["district"][0], "known")
        self.assertEqual(prov["proposed_uses"][0], "known")

    def test_build_use_context_unknown(self):
        ctx, prov = build_use_context()
        self.assertEqual(ctx, {"district": None, "proposed_uses": None})
        self.assertEqual(prov["district"][0], "unknown")
        self.assertEqual(prov["proposed_uses"][0], "unknown")
        self.assertIn("building program", prov["proposed_uses"][1])

    def test_unknown_program_key_loud(self):
        with self.assertRaises(ValueError) as cm:
            build_use_context(program={"proposed_usez": ["X"]})
        self.assertIn("unknown attributes", str(cm.exception))
        self.assertIn("proposed_usez", str(cm.exception))

    def test_proposed_uses_not_list_loud(self):
        with self.assertRaises(ValueError) as cm:
            build_use_context(program={"proposed_uses": "Agricultural use"})
        self.assertIn("proposed_uses", str(cm.exception))

    def test_proposed_uses_not_str_list_loud(self):
        with self.assertRaises(ValueError) as cm:
            build_use_context(program={"proposed_uses": ["Agricultural use", 42]})
        self.assertIn("proposed_uses", str(cm.exception))

    def test_per_scheme_override_merges(self):
        program = {
            "proposed_uses": ["Agricultural use"],
            "schemes": {"scheme-b": {"proposed_uses": ["Bar establishment"]}},
        }
        base, schemes_map = split_program(program)
        merged_b = program_for_scheme(base, schemes_map, "scheme-b")
        merged_a = program_for_scheme(base, schemes_map, "scheme-a")
        ctx_b, _ = build_use_context(
            zoning_cfg={"district": "M-1"}, program=merged_b)
        ctx_a, _ = build_use_context(
            zoning_cfg={"district": "M-1"}, program=merged_a)
        self.assertEqual(ctx_b["proposed_uses"], ["Bar establishment"])
        self.assertEqual(ctx_a["proposed_uses"], ["Agricultural use"])
        # End-to-end through the engine: override use is footnoted ->
        # MANUAL_REVIEW.
        pack = fixture_pack()
        res_b = evaluate_uses(ctx_b["district"], ctx_b["proposed_uses"], pack)
        res_a = evaluate_uses(ctx_a["district"], ctx_a["proposed_uses"], pack)
        self.assertEqual(res_b["verdict"], "MANUAL_REVIEW")
        self.assertEqual(res_a["verdict"], "PASS")


class EngineTest(unittest.TestCase):
    def setUp(self):
        self.pack = fixture_pack()

    def _by_use(self, res, use):
        for p in res["per_use"]:
            if p["use"] == use:
                return p
        self.fail(f"use {use!r} not in per_use")

    def test_permitted(self):
        res = evaluate_uses("M-1", ["Agricultural use"], self.pack)
        self.assertEqual(res["verdict"], "PASS")
        entry = self._by_use(res, "Agricultural use")
        self.assertEqual(entry["verdict"], "PASS")
        self.assertEqual(entry["rule_id"], "M1-U-02")
        self.assertEqual(entry["verified_by"], "Rohan")
        self.assertEqual(entry["verified_on"], "2026-09-23")

    def test_conditional_footnote_free(self):
        # NB: the plain M-1 U-13 row is shadowed by the FAIL
        # duplicate below; test the tie-break there. Here use a clean pack.
        pack = UsePack(
            rows=[make_row("M1-U-13", "M-1", "Raising of furbearing animals",
                           "C / P", "conditional")],
            fingerprint="single",
        )
        res = evaluate_uses("M-1", ["Raising of furbearing animals"], pack)
        self.assertEqual(res["verdict"], "CONDITIONAL_PASS")
        entry = res["per_use"][0]
        self.assertEqual(entry["verdict"], "CONDITIONAL_PASS")
        self.assertIn("conditional", entry["reason"])

    def test_footnotes_mean_manual_review(self):
        res = evaluate_uses("M-1", ["Bar establishment"], self.pack)
        self.assertEqual(res["verdict"], "MANUAL_REVIEW")
        entry = self._by_use(res, "Bar establishment")
        self.assertEqual(entry["verdict"], "MANUAL_REVIEW")
        self.assertIn("footnote(s) [6, 10]", entry["reason"])
        self.assertIn("manual review", entry["reason"])

    def test_m1_u28_unresolved(self):
        res = evaluate_uses(
            "M-1", ["Check cashing/payday loan business"], self.pack)
        self.assertEqual(res["verdict"], "UNKNOWN")
        entry = self._by_use(res, "Check cashing/payday loan business")
        self.assertEqual(entry["rule_id"], "M1-U-28")
        self.assertEqual(entry["verdict"], "UNKNOWN")
        self.assertIn("UNRESOLVED", entry["reason"])

    def test_os_u27_unresolved(self):
        res = evaluate_uses("OS", ["Reception center"], self.pack)
        self.assertEqual(res["verdict"], "UNKNOWN")
        entry = self._by_use(res, "Reception center")
        self.assertEqual(entry["rule_id"], "OS-U-27")
        self.assertIn("AMBIGUOUS", entry["reason"])

    def test_unknown_use_name(self):
        res = evaluate_uses("M-1", ["Moon base"], self.pack)
        self.assertEqual(res["verdict"], "UNKNOWN")
        entry = self._by_use(res, "Moon base")
        self.assertEqual(entry["verdict"], "UNKNOWN")
        self.assertIsNone(entry["rule_id"])
        self.assertEqual(entry["reason"], "no verified row for this use")

    def test_wrong_district_scoping(self):
        # "Reception center" exists only in OS; under M-1 it must not match.
        res = evaluate_uses("M-1", ["Reception center"], self.pack)
        entry = self._by_use(res, "Reception center")
        self.assertEqual(entry["verdict"], "UNKNOWN")
        self.assertIsNone(entry["rule_id"])
        self.assertEqual(entry["reason"], "no verified row for this use")
        # Case/whitespace-insensitive matching still scopes by district.
        res = evaluate_uses("M-1", ["  agricultural USE "], self.pack)
        entry = self._by_use(res, "  agricultural USE ")
        self.assertEqual(entry["rule_id"], "M1-U-02")

    def test_district_mu5_no_rows(self):
        # MU-5 now ships rows (Caddy's verified_uses_mu.json); a use with no
        # MU-5 row evaluates UNKNOWN per-use ("no verified row"), not the
        # district-level note.
        res = evaluate_uses("MU-5", ["Agricultural use"], self.pack)
        self.assertEqual(res["verdict"], "UNKNOWN")
        self.assertEqual(len(res["per_use"]), 1)
        self.assertIsNone(res["per_use"][0]["rule_id"])
        self.assertNotIn("no use rows for district", res["note"])

    def test_district_none(self):
        res = evaluate_uses(None, ["Agricultural use"], self.pack)
        self.assertEqual(res["verdict"], "UNKNOWN")
        self.assertEqual(res["per_use"], [])

    def test_empty_proposed_uses(self):
        for uses in (None, []):
            res = evaluate_uses("M-1", uses, self.pack)
            self.assertEqual(res["verdict"], "UNKNOWN")
            self.assertEqual(res["per_use"], [])
            self.assertEqual(res["note"],
                             "no proposed uses in program; use allowance "
                             "cannot be evaluated")

    def test_not_permitted_row(self):
        pack = UsePack(
            rows=[make_row("M1-U-29", "M-1",
                           "Chemical manufacturing and/or storage",
                           "C 19 (single mark)", "not_permitted")],
            fingerprint="single",
        )
        res = evaluate_uses("M-1", ["Chemical manufacturing and/or storage"],
                            pack)
        self.assertEqual(res["verdict"], "FAIL")
        entry = res["per_use"][0]
        self.assertEqual(entry["verdict"], "FAIL")
        self.assertIn("not permitted in M-1", entry["reason"])

    def test_unverified_row_gate(self):
        res = evaluate_uses("M-1", ["Hypothetical workshop"], self.pack)
        self.assertEqual(res["verdict"], "UNKNOWN")
        entry = self._by_use(res, "Hypothetical workshop")
        self.assertEqual(entry["verdict"], "UNKNOWN")
        self.assertEqual(entry["rule_id"], "M1-U-XX")
        self.assertIn("not human-verified", entry["reason"])
        self.assertIsNone(entry["verified_by"])

    def test_stale_status_cannot_authorize(self):
        # A row carrying a stale "verified"-looking flag but no human
        # verification record must still fail the gate.
        row = make_row("M1-U-ZZ", "M-1", "Stale workshop", "P", "permitted",
                       flags="status: verified", hv=None)
        pack = UsePack(rows=[row], fingerprint="single")
        res = evaluate_uses("M-1", ["Stale workshop"], pack)
        self.assertEqual(res["verdict"], "UNKNOWN")
        self.assertIn("not human-verified", res["per_use"][0]["reason"])

    def test_most_restrictive_tie_break(self):
        # Two M-1 rows for "Raising of furbearing animals": one
        # CONDITIONAL_PASS, one FAIL -> the use verdict is FAIL, tie noted.
        res = evaluate_uses("M-1", ["Raising of furbearing animals"], self.pack)
        self.assertEqual(res["verdict"], "FAIL")
        entry = self._by_use(res, "Raising of furbearing animals")
        self.assertEqual(entry["verdict"], "FAIL")
        self.assertIn("most restrictive", entry["reason"])
        self.assertIn("M1-U-13B", entry["reason"])

    def test_aggregation_order(self):
        # FAIL outranks UNKNOWN outranks MANUAL_REVIEW outranks
        # CONDITIONAL_PASS outranks PASS.
        pack_c = UsePack(
            rows=[
                make_row("M1-U-02", "M-1", "Agricultural use",
                         "P / P / P", "permitted"),
                make_row("M1-U-13", "M-1", "Raising of furbearing animals",
                         "C / P", "conditional"),
            ],
            fingerprint="c",
        )
        res = evaluate_uses(
            "M-1", ["Agricultural use", "Raising of furbearing animals"], pack_c)
        self.assertEqual(res["verdict"], "CONDITIONAL_PASS")
        res = evaluate_uses(
            "M-1", ["Agricultural use", "Moon base"], pack_c)
        self.assertEqual(res["verdict"], "UNKNOWN")
        # Footnoted use -> MANUAL_REVIEW; outranks CONDITIONAL_PASS but
        # loses to UNKNOWN. ("Agricultural use" is PASS in the fixture;
        # "Bar establishment" is footnoted.)
        res = evaluate_uses(
            "M-1", ["Agricultural use", "Bar establishment"],
            self.pack,
        )
        self.assertEqual(res["verdict"], "MANUAL_REVIEW")
        res = evaluate_uses(
            "M-1", ["Bar establishment", "Moon base"], self.pack)
        self.assertEqual(res["verdict"], "UNKNOWN")
        # "Raising of furbearing animals" hits the FAIL duplicate in the
        # full fixture -> FAIL outranks everything.
        res = evaluate_uses(
            "M-1", ["Agricultural use", "Raising of furbearing animals",
                    "Bar establishment", "Moon base"],
            self.pack,
        )
        self.assertEqual(res["verdict"], "FAIL")

    def test_mu_permitted_and_conditional(self):
        # MU rows flow through the same gate + vocabulary as M-1/OS/PL rows.
        pack = UsePack(
            rows=[
                make_row("MU5-U-001", "MU-5", "Brewpub", "P", "permitted"),
                make_row("MU5-U-096", "MU-5", "Nightclub", "C", "conditional"),
                make_row("MU11-U-050", "MU-11", "Brewpub", "C", "conditional"),
            ],
            fingerprint="mu-fixture",
        )
        for row in pack.rows:
            row.human_verification = {
                "result": "VERIFIED",
                "verified_by": "Rohan",
                "verified_on": "2026-09-23",
            }
        res = evaluate_uses("MU-5", ["Brewpub", "Nightclub"], pack)
        self.assertEqual(res["verdict"], "CONDITIONAL_PASS")  # most restrictive
        by_use = {p["use"]: p for p in res["per_use"]}
        self.assertEqual(by_use["Brewpub"]["verdict"], "PASS")
        self.assertEqual(by_use["Brewpub"]["rule_id"], "MU5-U-001")
        self.assertEqual(by_use["Nightclub"]["verdict"], "CONDITIONAL_PASS")
        # District scoping: MU-11's Brewpub row must not match under MU-5.
        res5 = evaluate_uses("MU-5", ["Brewpub"], pack)
        self.assertEqual(len(res5["per_use"]), 1)
        self.assertEqual(res5["per_use"][0]["rule_id"], "MU5-U-001")

    def test_mu_absent_use_is_unknown_never_fail(self):
        # A use absent from the MU lists evaluates UNKNOWN — the file's blank
        # cells have no rows, and extraction gaps must not read as FAIL.
        pack = UsePack(
            rows=[
                make_row("MU11-U-001", "MU-11", "Bakery", "P", "permitted"),
            ],
            fingerprint="mu-fixture",
        )
        for row in pack.rows:
            row.human_verification = {
                "result": "VERIFIED",
                "verified_by": "Rohan",
                "verified_on": "2026-09-23",
            }
        res = evaluate_uses("MU-11", ["Single-family (detached)"], pack)
        self.assertEqual(res["verdict"], "UNKNOWN")
        self.assertIsNone(res["per_use"][0]["rule_id"])

    def test_applicable_rows_counts_district(self):
        res = evaluate_uses("M-1", ["Agricultural use"], self.pack)
        self.assertEqual(
            res["applicable_rows"],
            sum(1 for r in self.pack.rows if r.district == "M-1"),
        )


@unittest.skipUnless(PACK_AVAILABLE, "pack.py not landed yet")
class RealPackIntegrationTest(unittest.TestCase):
    def test_real_pack_row_count_and_m1_u28(self):
        pack = load_pack()
        self.assertEqual(len(pack.rows), 191)
        res = evaluate_uses(
            "M-1", ["Check cashing/payday loan business"], pack)
        self.assertEqual(res["verdict"], "UNKNOWN")
        entry = next(
            p for p in res["per_use"]
            if p["rule_id"] == "M1-U-28")
        self.assertEqual(entry["verdict"], "UNKNOWN")
        self.assertIsNotNone(entry["verified_by"])


if __name__ == "__main__":
    unittest.main()
