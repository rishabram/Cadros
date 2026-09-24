"""Tests for the evidence/report.py extensions (wave-2 deep dives).

Covers: the machine-generated plain-English summary (section 0), geometry
notes in section 1, and the --preface/--append verbatim injection hooks.

All summary assertions are computed from the source report.json — the tests
pin the "no invented facts" property, not specific demo numbers.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PY = os.path.join(REPO, "venv", "bin", "python")
STORE = os.path.join(REPO, "rulegraph", "verified_rules.json")

sys.path.insert(0, REPO)
from evidence import report as R  # noqa: E402


def _fresh_demo_report_json():
    outdir = tempfile.mkdtemp(prefix="evid_sum_test_")
    subprocess.run(
        [PY, os.path.join(REPO, "run.py"), "--parcel",
         os.path.join(REPO, "inputs", "demo_parcel.geojson"),
         "--out", outdir],
        check=True, capture_output=True,
    )
    return os.path.join(outdir, "report.json")


def _synthetic_report(district, rule_evals, verdicts):
    """Minimal report.json-shaped dict for summary logic tests."""
    schemes = [{
        "scheme_id": "scheme_00",
        "lots": 4,
        "road_ft": 500.0,
        "clean": True,
        "proforma": {
            "lot_count": 4, "road_length_ft": 500.0, "revenue": 1800000.0,
            "total_cost": 400000.0, "profit": 1400000.0, "margin": 0.7778,
            "assumptions": {"source": "synthetic test"},
        },
        "rulegraph": rule_evals,
        "rulegraph_verdict": "UNKNOWN" if any(r["outcome"] == "UNKNOWN" for r in rule_evals) else "PASS",
    }]
    return {
        "parcel_id": "TEST000000000000",
        "status": "ok",
        "parcel_area_sqft": 100000.0,
        "parcel_area_acres": 2.2957,
        "crs": "EPSG:26912",
        "zoning": {"district": district, "source": "synthetic test",
                   "zone_label": district},
        "finance_assumptions": {"economics": {"revenue_confidence": "assumption",
                                              "revenue_source": "synthetic test"}},
        "schemes": schemes,
        "ranked_order": ["scheme_00"],
        "rulegraph": {
            "rules_evaluated": len(rule_evals),
            "scheme_verdicts": verdicts,
            "gaps": [{"attribute": "height_ft", "needed_from": "building plans"}],
            "context_provenance": {},
            "program_supplied": False,
        },
    }


def _rule(rid, outcome, applicable, reason="test reason"):
    return {"rule_id": rid, "outcome": outcome, "applicable": applicable,
            "reason": reason}


class SummarySectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report_json = _fresh_demo_report_json()
        with open(cls.report_json) as f:
            cls.report = json.load(f)
        cls.tmp = tempfile.mkdtemp(prefix="evid_sum_md_")
        cls.md_path = os.path.join(cls.tmp, "summary_report.md")
        R.generate(cls.report_json, STORE, cls.md_path)
        with open(cls.md_path) as f:
            cls.md = f.read()

    def test_section_0_present_before_section_1(self):
        self.assertIn("## 0. What this means (plain-English summary)", self.md)
        self.assertLess(self.md.index("## 0."),
                        self.md.index("## 1. Parcel facts"))

    def test_summary_echoes_source_figures_exactly(self):
        sec0 = self.md[self.md.index("## 0."):self.md.index("## 1.")]
        # parcel id, acres, and top-scheme profit/margin copied from report.json
        self.assertIn(self.report["parcel_id"], sec0)
        top_id = self.report["ranked_order"][0]
        top = {s["scheme_id"]: s for s in self.report["schemes"]}[top_id]
        pf = top["proforma"]
        self.assertIn(R._money(pf["profit"]), sec0)
        self.assertIn(R._pct(pf["margin"]), sec0)
        self.assertIn(top_id, sec0)

    def test_summary_carries_verdict_counts(self):
        sec0 = self.md[self.md.index("## 0."):self.md.index("## 1.")]
        v = self.report["rulegraph"]["scheme_verdicts"]
        for k in ("PASS", "FAIL", "UNKNOWN"):
            self.assertIn(str(v.get(k, 0)), sec0)

    def test_summary_is_machine_labeled_not_a_recommendation(self):
        sec0 = self.md[self.md.index("## 0."):self.md.index("## 1.")]
        self.assertIn("Machine-generated", sec0)
        self.assertIn("not a recommendation", sec0.lower())
        self.assertNotIn("we recommend", sec0.lower())
        self.assertNotIn("you should", sec0.lower())

    def test_exact_number_formatting_no_rounding_beyond_source(self):
        self.assertEqual(R._num(None), "n/a")
        self.assertEqual(R._num(994.8), "994.8")
        self.assertEqual(R._num(331.0), "331")
        self.assertEqual(R._num(5), "5")
        # road figure in the summary must show the source value, not a rounded one
        sec0 = self.md[self.md.index("## 0."):self.md.index("## 1.")]
        top_id = self.report["ranked_order"][0]
        top = {s["scheme_id"]: s for s in self.report["schemes"]}[top_id]
        road = top["proforma"].get("road_length_ft", top.get("road_ft"))
        self.assertIn(R._num(road), sec0)

    def test_geometry_notes_in_section_1(self):
        sec1 = self.md[self.md.index("## 1."):self.md.index("## 2.")]
        self.assertIn("geometry notes", sec1)
        n_clean = sum(1 for s in self.report["schemes"] if s.get("clean") is True)
        self.assertIn(str(n_clean), sec1)

    def test_vacuous_pass_caveat_when_no_rule_applies(self):
        evals = [_rule("MU-11-05", "PASS", False, "not applicable: district"),
                 _rule("PL-04", "PASS", False, "not applicable: district")]
        rep = _synthetic_report("M-1", evals, {"PASS": 1, "FAIL": 0, "UNKNOWN": 0})
        sec0 = R._section_0(rep)
        self.assertIn("None of the store's rules apply to the M-1 district", sec0)
        self.assertIn("not 'compliant'", sec0)

    def test_unknown_bottom_line_when_applicable_rules_unknown(self):
        evals = [_rule("MU-11-05", "UNKNOWN", True, "building form is unknown"),
                 _rule("MU-11-11", "PASS", True, "no minimum")]
        rep = _synthetic_report("MU-11", evals, {"PASS": 0, "FAIL": 0, "UNKNOWN": 1})
        sec0 = R._section_0(rep)
        self.assertIn("`MU-11-05`", sec0)
        self.assertIn("no scheme on this parcel has a confirmed compliance", sec0.lower())

    def test_pass_with_applicable_rules_notes_unknown_attributes(self):
        evals = [_rule("MU-11-11", "PASS", True, "no minimum")]
        rep = _synthetic_report("MU-11", evals, {"PASS": 1, "FAIL": 0, "UNKNOWN": 0})
        sec0 = R._section_0(rep)
        self.assertIn("not a compliance finding", sec0)


class PrefaceAppendTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report_json = _fresh_demo_report_json()
        cls.tmp = tempfile.mkdtemp(prefix="evid_pa_md_")
        cls.preface = os.path.join(cls.tmp, "preface.md")
        cls.append = os.path.join(cls.tmp, "append.md")
        with open(cls.preface, "w") as f:
            f.write("## Deep-dive narrative\n\nPREFACE-MARKER-123\n")
        with open(cls.append, "w") as f:
            f.write("## Analyst notes\n\nAPPEND-MARKER-456\n")
        cls.md_path = os.path.join(cls.tmp, "pa_report.md")
        R.generate(cls.report_json, STORE, cls.md_path,
                   preface_md_path=cls.preface, append_md_path=cls.append)
        with open(cls.md_path) as f:
            cls.md = f.read()

    def test_preface_after_banner_before_section_0(self):
        self.assertIn("PREFACE-MARKER-123", self.md)
        self.assertLess(self.md.index("PREFACE-MARKER-123"),
                        self.md.index("## 0."))
        self.assertGreater(self.md.index("PREFACE-MARKER-123"),
                           self.md.index("machine-draft"))

    def test_append_before_footer_after_section_6(self):
        self.assertIn("APPEND-MARKER-456", self.md)
        self.assertLess(self.md.index("## 6."), self.md.index("APPEND-MARKER-456"))
        self.assertLess(self.md.index("APPEND-MARKER-456"),
                        self.md.index("## 7. Provenance footer"))

    def test_preface_append_are_verbatim(self):
        self.assertIn("## Deep-dive narrative", self.md)
        self.assertIn("## Analyst notes", self.md)

    def test_cli_preface_append_flags(self):
        out = os.path.join(self.tmp, "cli_pa.md")
        res = subprocess.run(
            [PY, "-m", "evidence.report", self.report_json,
             "--store", STORE, "--out", out,
             "--preface", self.preface, "--append", self.append],
            cwd=REPO, capture_output=True, text=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        with open(out) as f:
            md = f.read()
        self.assertIn("PREFACE-MARKER-123", md)
        self.assertIn("APPEND-MARKER-456", md)


if __name__ == "__main__":
    unittest.main(verbosity=2)
