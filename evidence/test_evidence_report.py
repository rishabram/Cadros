"""Tests for the W4 evidence report generator.

Asserts: all sections present; every UNKNOWN surfaced in section 5; quotes
match the store verbatim; footer fingerprint matches the recomputed engine
fingerprint; and the report never introduces a verdict of its own (it only
describes store records).
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
REPORT_JSON = os.path.join(REPO, "inputs", "..", "outputs", "demo", "report.json") \
    if False else None
STORE = os.path.join(REPO, "rulegraph", "verified_rules.json")


def _fresh_demo_report_json():
    """Build a fresh demo report.json via the real pipeline so the evidence
    report is tested against current pipeline output."""
    outdir = tempfile.mkdtemp(prefix="evid_test_")
    subprocess.run(
        [PY, os.path.join(REPO, "run.py"), "--parcel",
         os.path.join(REPO, "inputs", "demo_parcel.geojson"),
         "--out", outdir],
        check=True, capture_output=True,
    )
    return os.path.join(outdir, "report.json")


def _section(md, num):
    start = md.index("## {}.".format(num))
    nxt = md.find("## {}.".format(num + 1), start)
    return md[start:nxt] if nxt != -1 else md[start:]


class EvidenceReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report_json = _fresh_demo_report_json()
        with open(cls.report_json) as f:
            cls.report = json.load(f)
        with open(STORE) as f:
            cls.store = json.load(f)
        cls.rules = cls.store["rules"]
        if isinstance(cls.rules, dict):
            cls.rules = {k: v for k, v in cls.rules.items()}
        else:
            cls.rules = {r["rule_id"]: r for r in cls.rules}
        cls.tmp = tempfile.mkdtemp(prefix="evid_md_")
        cls.md_path = os.path.join(cls.tmp, "evidence_report.md")
        from evidence.report import generate
        generate(cls.report_json, STORE, cls.md_path)
        with open(cls.md_path) as f:
            cls.md = f.read()

    def test_all_sections_present(self):
        titles = ["Parcel facts", "Scheme ranking table", "Per-scheme RuleGraph verdicts",
                  "Economics breakdown", "Gaps & unknowns", "Use allowance",
                  "Provenance footer"]
        for i, t in enumerate(titles, start=1):
            self.assertIn("## {}. {}".format(i, t), self.md,
                          "missing section {}: {}".format(i, t))

    def test_every_unknown_gap_attribute_in_section_5(self):
        sec5 = _section(self.md, 5)
        gaps = self.report["rulegraph"]["gaps"]
        self.assertTrue(gaps, "expected gaps in demo report")
        for g in gaps:
            self.assertIn(g["attribute"], sec5,
                          "UNKNOWN attribute {} not surfaced in section 5".format(g["attribute"]))

    def test_every_unknown_rule_outcome_in_section_5(self):
        sec5 = _section(self.md, 5)
        schemes = {s["scheme_id"]: s for s in self.report["schemes"]}
        for sid in self.report["ranked_order"]:
            unk = [r["rule_id"] for r in schemes[sid]["rulegraph"]
                   if r["outcome"] == "UNKNOWN"]
            for rid in unk:
                self.assertIn(rid, sec5,
                              "UNKNOWN rule {} of {} not surfaced in section 5".format(rid, sid))

    def test_unknowns_prominent_not_buried(self):
        sec3 = _section(self.md, 3)
        # Every UNKNOWN verdict must carry the prominent marker in section 3.
        n_marked = sec3.count("⚠ UNKNOWN")
        self.assertGreater(n_marked, 0)
        schemes = {s["scheme_id"]: s for s in self.report["schemes"]}
        n_unknown = sum(1 for sid in self.report["ranked_order"]
                        for r in schemes[sid]["rulegraph"] if r["outcome"] == "UNKNOWN")
        self.assertGreaterEqual(n_marked, n_unknown)

    def test_quotes_match_store_verbatim(self):
        # Only applicable rules get full evidence blocks (non-applicable
        # rules are summarized, not quoted in full).
        schemes = {s["scheme_id"]: s for s in self.report["schemes"]}
        top = schemes[self.report["ranked_order"][0]]
        applicable = {r["rule_id"] for r in top["rulegraph"]
                      if r.get("applicable") is True}
        self.assertTrue(applicable, "expected applicable rules on demo top scheme")
        for rid in applicable:
            quote = self.rules[rid].get("quote") or self.rules[rid].get("source_quote")
            self.assertIsNotNone(quote, f"no quote field on {rid}")
            self.assertIn(quote, self.md,
                          "verbatim quote for {} missing from report".format(rid))
        sec3 = _section(self.md, 3)
        self.assertIn("district-scoped out", sec3)

    def test_human_verification_described_not_invented(self):
        # The report may only echo the store's human_verification record,
        # for the applicable rules it quotes.
        schemes = {s["scheme_id"]: s for s in self.report["schemes"]}
        top = schemes[self.report["ranked_order"][0]]
        applicable = [r["rule_id"] for r in top["rulegraph"]
                      if r.get("applicable") is True]
        self.assertTrue(applicable, "expected applicable rules on demo top scheme")
        for rid in applicable:
            hv = self.rules[rid].get("human_verification", {})
            self.assertIn(hv.get("verified_by", ""), self.md)
            self.assertIn(hv.get("verified_on", ""), self.md)
            self.assertIn("Human verification (described from store record", self.md)
        # Report must never claim to grant a verdict itself.
        self.assertNotIn("verified by this report", self.md.lower())
        self.assertNotIn("verdict granted", self.md.lower())

    def test_fingerprint_in_footer_matches_recomputed(self):
        from evidence.report import store_fingerprint
        expected = store_fingerprint(self.store)
        recorded = self.report["rulegraph"]["store_fingerprint"]
        self.assertEqual(expected, recorded)
        self.assertIn(expected, _section(self.md, 7))
        self.assertIn("MATCH", _section(self.md, 7))

    def test_machine_draft_label(self):
        self.assertIn("machine-draft — not human-verified output", self.md)

    def test_use_allowance_section_integrated(self):
        # Use allowance is now really integrated (machine-evaluated against
        # the human-verified packs), not a placeholder.
        sec6 = _section(self.md, 6)
        self.assertIn("machine-evaluated", sec6)
        self.assertIn("m1_os_pl", sec6)
        self.assertIn("mu", sec6)
        self.assertIn("5a3a06db", sec6)  # M-1/OS/PL pack fingerprint
        self.assertIn("bf741fd2", sec6)  # MU pack fingerprint
        self.assertIn("No building program was supplied", sec6)
        self.assertIn("UNKNOWN by design", sec6)
        self.assertIn("never treated as allowed", sec6)
        self.assertNotIn("not yet integrated", sec6)

    def test_cli_smoke(self):
        out = os.path.join(self.tmp, "cli_report.md")
        res = subprocess.run(
            [PY, "-m", "evidence.report", self.report_json,
             "--store", STORE, "--out", out],
            cwd=REPO, capture_output=True, text=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertTrue(os.path.exists(out))
        with open(out) as f:
            self.assertIn("## 1. Parcel facts", f.read())


if __name__ == "__main__":
    unittest.main(verbosity=2)
