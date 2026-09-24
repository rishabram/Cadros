"""Tests for honest RuleGraph verdict language in evidence reports.

Benchmark finding #2: a scheme verdict of PASS with zero applicable rules
(all district-scoped out) read as compliance confirmation. These tests pin:
  - vacuous PASS renders as "PASS — no applicable rules in the canonical
    store (district not covered; compliance NOT confirmed)",
  - genuine PASS renders "PASS — evaluated against N applicable rules",
  - legacy reports (pre-dating the pipeline's rulegraph_applicable_rules
    field) still render honestly via fallback counting,
  - the Section 2 ranking table never shows a bare PASS either.

Mirrors screen/screener.py's rg_verdict_basis semantics: "evaluated" /
"no_applicable_rules". The verdict enum itself is never relabeled.

Produces and implies no human verdicts.
"""
from __future__ import annotations

import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from evidence import report as R


def _scheme(sid, verdict, applicable_rules=None, rule_list=None):
    s = {
        "scheme_id": sid,
        "lots": 4,
        "road_ft": 500.0,
        "clean": True,
        "proforma": {"lot_count": 4, "road_length_ft": 500.0,
                     "revenue": 1800000.0, "total_cost": 400000.0,
                     "profit": 1400000.0, "margin": 0.7778,
                     "assumptions": {"source": "test"}},
        "rulegraph_verdict": verdict,
        "rulegraph": rule_list or [],
    }
    if applicable_rules is not None:
        s["rulegraph_applicable_rules"] = applicable_rules
    return s


def _rule(rid, outcome, applicable):
    return {"rule_id": rid, "outcome": outcome, "applicable": applicable,
            "reason": "test", "status": "VERIFIED"}


def _report(schemes):
    return {
        "parcel_id": "TEST000000000000",
        "status": "ok",
        "parcel_area_sqft": 100000.0,
        "parcel_area_acres": 2.2957,
        "crs": "local-feet",
        "zoning": {"district": "M-1", "source": "test", "zone_label": "M-1"},
        "finance_assumptions": {},
        "ranked_order": [s["scheme_id"] for s in schemes],
        "schemes": schemes,
        "rulegraph": {"store": "rulegraph/verified_rules.json",
                      "store_fingerprint": "x", "rules_evaluated": 8,
                      "program_supplied": False,
                      "scheme_verdicts": {"PASS": 1, "FAIL": 0, "UNKNOWN": 0},
                      "gaps": [], "context_provenance": {},
                      "note": "test"},
    }


class TestVerdictLanguage(unittest.TestCase):
    def test_vacuous_pass_renders_no_applicable_rules(self):
        rules = [_rule(f"R-{i}", "PASS", False) for i in range(8)]
        s = _scheme("scheme_00", "PASS", applicable_rules=0, rule_list=rules)
        html = R._render_scheme_verdict(s)
        self.assertIn("no applicable rules in the canonical store", html)
        self.assertIn("compliance NOT confirmed", html)
        self.assertNotIn("evaluated against", html)

    def test_genuine_pass_names_rule_count(self):
        rules = ([_rule(f"R-{i}", "PASS", True) for i in range(3)]
                 + [_rule(f"R-{i}", "PASS", False) for i in range(3, 8)])
        s = _scheme("scheme_00", "PASS", applicable_rules=3, rule_list=rules)
        html = R._render_scheme_verdict(s)
        self.assertIn("**PASS — evaluated against 3 applicable rules**", html)
        self.assertNotIn("no applicable", html)

    def test_legacy_report_falls_back_to_rule_list_count(self):
        # no 'rulegraph_applicable_rules' key: count applicable:true instead
        rules = ([_rule("R-1", "PASS", True)]
                 + [_rule(f"R-{i}", "PASS", False) for i in range(2, 8)])
        s = _scheme("scheme_00", "PASS", applicable_rules=None, rule_list=rules)
        html = R._render_scheme_verdict(s)
        self.assertIn("**PASS — evaluated against 1 applicable rule**", html)
        self.assertNotIn("rules", html)

    def test_legacy_vacuous_pass_still_honest(self):
        rules = [_rule(f"R-{i}", "PASS", False) for i in range(8)]
        s = _scheme("scheme_00", "PASS", applicable_rules=None, rule_list=rules)
        html = R._render_scheme_verdict(s)
        self.assertIn("no applicable rules in the canonical store", html)
        self.assertIn("compliance NOT confirmed", html)

    def test_fail_and_unknown_verdicts_unchanged(self):
        s = _scheme("scheme_00", "FAIL", applicable_rules=2,
                    rule_list=[_rule("R-1", "FAIL", True)])
        self.assertEqual(R._render_scheme_verdict(s), "**FAIL**")
        s = _scheme("scheme_00", "UNKNOWN", applicable_rules=2,
                    rule_list=[_rule("R-1", "UNKNOWN", True)])
        self.assertEqual(R._render_scheme_verdict(s), "**UNKNOWN**")

    def test_section_3_uses_honest_headers(self):
        vacuous = _scheme("scheme_00", "PASS", applicable_rules=0,
                          rule_list=[_rule("R-1", "PASS", False)])
        genuine = _scheme("scheme_01", "PASS", applicable_rules=2,
                          rule_list=[_rule("R-1", "PASS", True),
                                     _rule("R-2", "PASS", True)])
        text = R._section_3(_report([vacuous, genuine]), {}, {})
        self.assertIn("no applicable rules in the canonical store", text)
        self.assertIn("**PASS — evaluated against 2 applicable rules**", text)

    def test_section_2_table_never_shows_bare_pass(self):
        vacuous = _scheme("scheme_00", "PASS", applicable_rules=0,
                          rule_list=[_rule("R-1", "PASS", False)])
        genuine = _scheme("scheme_01", "PASS", applicable_rules=2,
                          rule_list=[_rule("R-1", "PASS", True),
                                     _rule("R-2", "PASS", True)])
        text = R._section_2(_report([vacuous, genuine]))
        # no cell may contain exactly "| PASS |" for the rg-verdict column
        for line in text.splitlines():
            if line.startswith("|") and "scheme_0" in line:
                self.assertNotRegex(line, r"\| PASS \|")
        self.assertIn("no applicable rules in the canonical store", text)
        self.assertIn("**PASS — evaluated against 2 applicable rules**", text)


if __name__ == "__main__":
    unittest.main()
