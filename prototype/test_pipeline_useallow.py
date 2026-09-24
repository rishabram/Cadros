"""Use-allowance wiring in the pipeline report.

Covers: the report-level "use_allowance" block, per-scheme "use_verdict" /
"use_applicable_rows" / "use_allowance" keys, the no-program UNKNOWN case
(reason "no proposed uses"), footnote-carrying uses -> UNKNOWN manual
review, per-scheme program overrides, and typo loudness end to end.

Run: venv/bin/python -m unittest prototype.test_pipeline_useallow -v
(from the repo root)
"""
import json
import tempfile
import unittest

from useallow import engine as use_engine
from useallow import pack as use_pack
from .pipeline import run_pipeline


def _run(program):
    tmp = tempfile.TemporaryDirectory()
    # addCleanup ordering: TemporaryDirectory.cleanup runs after the test.
    return tmp, run_pipeline(
        "inputs/demo_parcel.geojson", "inputs/zoning.json",
        "inputs/finance.json", tmp.name, max_schemes=8,
        building_program=program,
    )["report"]


class TestUseAllowanceWiring(unittest.TestCase):
    def test_with_program_block_and_per_scheme_keys(self):
        tmp, report = _run({
            "district": "M-1",
            "proposed_uses": ["Agricultural use", "Bar establishment"],
        })
        try:
            ua = report["use_allowance"]
            self.assertIn("21A33_candidates_M1_OS_PL.md", ua["pack"])
            self.assertIn("verified_uses_mu.json", ua["pack"])
            # Combined 513-row pack (191 M-1/OS/PL + 322 MU) with a fresh
            # fingerprint; component fingerprints stay individually pinned.
            from useallow import mu_pack

            self.assertEqual(
                ua["pack_fingerprint"],
                use_pack.combine_packs(
                    use_pack.load_pack(), mu_pack.load_mu_pack()
                ).fingerprint,
            )
            self.assertEqual(
                ua["pack_fingerprints"]["m1_os_pl"],
                use_pack.load_pack().fingerprint,
            )
            self.assertEqual(
                ua["pack_fingerprints"]["mu"],
                mu_pack.load_mu_pack().fingerprint,
            )
            self.assertEqual(ua["rows_parsed"], 513)
            self.assertTrue(ua["program_supplied"])
            self.assertTrue(ua["proposed_uses_present"])
            self.assertNotIn("per_scheme_program", ua)
            self.assertIn("UNKNOWN never means allowed", ua["note"])
            self.assertIn("blank-cell code facts", ua["note"])

            self.assertEqual(len(report["schemes"]), 8)
            # Bar establishment carries footnotes 6,10 -> MANUAL_REVIEW, so
            # every scheme verdict is MANUAL_REVIEW (it outranks PASS).
            self.assertEqual(
                ua["scheme_verdicts"],
                {"PASS": 0, "CONDITIONAL_PASS": 0, "FAIL": 0,
                 "UNKNOWN": 0, "MANUAL_REVIEW": 8},
            )
            for s in report["schemes"]:
                self.assertEqual(s["use_verdict"], "MANUAL_REVIEW",
                                 s["scheme_id"])
                self.assertEqual(s["use_applicable_rows"], 122, s["scheme_id"])
                by_use = {p["use"]: p for p in s["use_allowance"]}
                self.assertEqual(by_use["Agricultural use"]["verdict"], "PASS")
                self.assertEqual(by_use["Agricultural use"]["rule_id"], "M1-U-02")
                bar = by_use["Bar establishment"]
                self.assertEqual(bar["verdict"], "MANUAL_REVIEW")
                self.assertEqual(bar["rule_id"], "M1-U-03")
                self.assertIn("manual review", bar["reason"])
                self.assertEqual(bar["verified_by"], "Rohan")
        finally:
            tmp.cleanup()

    def test_mu11_program_uses_end_to_end(self):
        # MU-11 program with a permitted and a conditional use exercises the
        # merged 513-row pack: 111 MU-11 rows scope in, district vocabulary
        # maps permitted->PASS and conditional->CONDITIONAL_PASS.
        tmp, report = _run({
            "district": "MU-11",
            "proposed_uses": ["Brewery", "Kennel"],
        })
        try:
            ua = report["use_allowance"]
            self.assertEqual(ua["rows_parsed"], 513)
            self.assertEqual(ua["scheme_verdicts"]["CONDITIONAL_PASS"], 8)
            s0 = report["schemes"][0]
            self.assertEqual(s0["use_verdict"], "CONDITIONAL_PASS")
            self.assertEqual(s0["use_applicable_rows"], 111)
            by_use = {p["use"]: p for p in s0["use_allowance"]}
            self.assertEqual(by_use["Brewery"]["verdict"], "PASS")
            self.assertTrue(by_use["Brewery"]["rule_id"].startswith("MU11-U-"))
            self.assertEqual(by_use["Brewery"]["verified_by"], "Rohan")
            self.assertEqual(by_use["Kennel"]["verdict"], "CONDITIONAL_PASS")
        finally:
            tmp.cleanup()

    def test_without_program_all_unknown(self):
        tmp, report = _run(None)
        try:
            ua = report["use_allowance"]
            self.assertFalse(ua["program_supplied"])
            self.assertFalse(ua["proposed_uses_present"])
            self.assertNotIn("per_scheme_program", ua)
            for s in report["schemes"]:
                self.assertEqual(s["use_verdict"], "UNKNOWN", s["scheme_id"])
                self.assertEqual(s["use_allowance"], [], s["scheme_id"])
            # The actionable reason, checked at the engine level: no
            # proposed uses (even though the district is also missing).
            res = use_engine.evaluate_uses(None, None, use_pack.load_pack())
            self.assertEqual(res["verdict"], "UNKNOWN")
            self.assertIn("no proposed uses", res["note"])
        finally:
            tmp.cleanup()

    def test_per_scheme_override(self):
        tmp, report = _run({
            "district": "M-1",
            "proposed_uses": ["Agricultural use"],
            "schemes": {
                "scheme_00": {
                    "proposed_uses": ["Chemical manufacturing and/or storage"]
                },
            },
        })
        try:
            ua = report["use_allowance"]
            self.assertTrue(ua["per_scheme_program"])
            self.assertTrue(ua["proposed_uses_present"])
            verdicts = {s["scheme_id"]: s["use_verdict"] for s in report["schemes"]}
            # scheme_00's use is a blank-cell code fact -> FAIL.
            self.assertEqual(verdicts["scheme_00"], "FAIL")
            scheme_00 = next(
                s for s in report["schemes"] if s["scheme_id"] == "scheme_00"
            )
            entry = next(
                p for p in scheme_00["use_allowance"]
                if p["use"] == "Chemical manufacturing and/or storage"
            )
            self.assertEqual(entry["rule_id"], "M1-U-29")
            self.assertIn("not permitted", entry["reason"])
            for sid, v in verdicts.items():
                if sid != "scheme_00":
                    self.assertEqual(v, "PASS", sid)
        finally:
            tmp.cleanup()

    def test_mixed_rulegraph_and_use_program(self):
        # The shared building program may carry RuleGraph facts AND
        # proposed_uses; each adapter ignores the other's keys.
        with open("inputs/demo_program.json") as f:
            base = json.load(f)
        tmp, report = _run({
            **base,  # district MU-11 + RuleGraph facts
            "proposed_uses": ["Agricultural use"],
        })
        try:
            # MU-11 now has 111 verified use rows (Caddy's pack), but
            # "Agricultural use" matches none of them -> UNKNOWN per use,
            # honestly (no verified row, never FAIL).
            for s in report["schemes"]:
                self.assertEqual(s["use_verdict"], "UNKNOWN", s["scheme_id"])
                self.assertEqual(s["use_applicable_rows"], 111, s["scheme_id"])
            self.assertTrue(report["use_allowance"]["proposed_uses_present"])
            # RuleGraph wiring is unaffected by the foreign key. Caddy
            # extraction v2 made MU-11-01..04 executable; the demo program's
            # 8 ft rear setback honestly FAILs MU-11-04 on every scheme.
            self.assertEqual(
                report["rulegraph"]["scheme_verdicts"]["FAIL"], 8
            )
        finally:
            tmp.cleanup()

    def test_typo_program_key_is_loud(self):
        tmp = tempfile.TemporaryDirectory()
        try:
            with self.assertRaises(ValueError) as cm:
                run_pipeline(
                    "inputs/demo_parcel.geojson", "inputs/zoning.json",
                    "inputs/finance.json", tmp.name, max_schemes=8,
                    building_program={"district": "M-1",
                                      "proposed_usez": ["X"]},
                )
            self.assertIn("unknown attributes", str(cm.exception))
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
