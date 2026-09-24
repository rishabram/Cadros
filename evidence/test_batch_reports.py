"""Tests for batch per-parcel evidence reports (canonical re-screen wave).

Covers: determinism (byte-identical regeneration), fingerprint surfacing
(rule store recomputed, use-pack fingerprints echoed), no-scheme parcels
getting a named diagnostic (never omitted), explicit UNKNOWN language,
no invented verdicts, explicit error reports, and the batch runner covering
every parcel with nothing silently skipped.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from evidence import report as R  # noqa: E402
from evidence import batch as B  # noqa: E402

STORE = os.path.join(REPO, "rulegraph", "verified_rules.json")
SCREEN = os.path.join(REPO, "screen", "outputs", "real_slco_v3")
# One scheme parcel (M-1) and one no-scheme parcel from the real screen.
SCHEME_PID = "08214000240000"
NOSCHEME_PID = "08223510140000"


def _load(pid):
    with open(os.path.join(SCREEN, pid, "report.json")) as f:
        return json.load(f)


def _load_store():
    with open(STORE) as f:
        return json.load(f)


class DeterminismTest(unittest.TestCase):
    def test_regeneration_is_byte_identical(self):
        store = _load_store()
        for pid in (SCHEME_PID, NOSCHEME_PID):
            rep = _load(pid)
            a = R.generate_from_objects(rep, store)
            b = R.generate_from_objects(rep, store)
            self.assertEqual(a, b, "non-deterministic report for {}".format(pid))

    def test_no_wall_clock_timestamps(self):
        store = _load_store()
        md = R.generate_from_objects(_load(SCHEME_PID), store)
        self.assertNotIn("Generated (UTC)", md)


class FingerprintTest(unittest.TestCase):
    def test_rule_store_fingerprint_recomputed_and_matched(self):
        store = _load_store()
        md = R.generate_from_objects(_load(SCHEME_PID), store)
        expected = R.store_fingerprint(store)
        self.assertIn(expected, md)
        self.assertIn("Fingerprint check: MATCH", md)

    def test_use_pack_fingerprints_surfaced(self):
        store = _load_store()
        md = R.generate_from_objects(_load(SCHEME_PID), store)
        self.assertIn("5a3a06db", md)  # M-1/OS/PL pack pin
        self.assertIn("bf741fd2", md)  # MU pack pin
        self.assertIn("02a78aa4", md)  # combined pack pin

    def test_report_json_fingerprint_in_footer(self):
        store = _load_store()
        rep = _load(SCHEME_PID)
        md = R.generate_from_objects(rep, store)
        self.assertIn(R.report_fingerprint(rep), md)


class NoSchemeTest(unittest.TestCase):
    def test_no_scheme_parcel_names_its_diagnostic(self):
        store = _load_store()
        md = R.generate_from_objects(_load(NOSCHEME_PID), store)
        rep = _load(NOSCHEME_PID)
        verdict = rep["scheme_generation"]["verdict"]
        self.assertIn(verdict, md)
        self.assertIn("No schemes were drawn", md)

    def test_no_scheme_report_makes_no_scheme_claims(self):
        store = _load_store()
        md = R.generate_from_objects(_load(NOSCHEME_PID), store)
        self.assertIn("no schemes were drawn, so no rules were evaluated", md)
        self.assertIn("no economics were computed", md)
        # The scheme-parcel summary sentence ("lays out N lots") is absent.
        self.assertNotIn("lays out", md)


class UnknownLanguageTest(unittest.TestCase):
    def test_unknowns_prominent(self):
        store = _load_store()
        md = R.generate_from_objects(_load(SCHEME_PID), store)
        self.assertIn("⚠ UNKNOWN", md)

    def test_unknown_never_treated_as_allowed(self):
        store = _load_store()
        md = R.generate_from_objects(_load(SCHEME_PID), store)
        self.assertIn("never treated as allowed", md)
        self.assertIn("UNKNOWN is never treated as a pass", md)

    def test_machine_draft_banner_visible(self):
        store = _load_store()
        for pid in (SCHEME_PID, NOSCHEME_PID):
            md = R.generate_from_objects(_load(pid), store)
            self.assertIn("machine-draft — not human-verified output", md)


class NoInventedVerdictsTest(unittest.TestCase):
    def test_human_verification_only_echoed(self):
        store = _load_store()
        rules = R._key_rules(store)
        rep = _load(SCHEME_PID)
        top = {s["scheme_id"]: s for s in rep["schemes"]}[rep["ranked_order"][0]]
        applicable = [r["rule_id"] for r in top["rulegraph"]
                      if r.get("applicable") is True]
        md = R.generate_from_objects(rep, store)
        for rid in applicable:
            hv = rules[rid].get("human_verification", {})
            self.assertIn(hv.get("verified_by", ""), md)
            self.assertIn(hv.get("verified_on", ""), md)
        self.assertNotIn("verified by this report", md.lower())
        self.assertNotIn("verdict granted", md.lower())
        self.assertNotIn("we verify", md.lower())


class ErrorReportTest(unittest.TestCase):
    def test_error_report_is_explicit(self):
        md = R.generate_error_report("PID123", "ValueError: boom", district="M-1")
        self.assertIn("ERROR", md)
        self.assertIn("ValueError: boom", md)
        self.assertIn("PID123", md)
        self.assertIn("machine-draft — not human-verified output", md)
        self.assertIn("Not computed", md)


class BatchRunnerTest(unittest.TestCase):
    def test_batch_covers_every_parcel_nothing_skipped(self):
        tmp = tempfile.mkdtemp(prefix="evid_batch_test_")
        screen = os.path.join(tmp, "screen")
        os.makedirs(screen)
        for pid in (SCHEME_PID, NOSCHEME_PID):
            d = os.path.join(screen, pid)
            os.makedirs(d)
            shutil.copy(os.path.join(SCREEN, pid, "report.json"),
                        os.path.join(d, "report.json"))
        with open(os.path.join(screen, "summary.json"), "w") as f:
            json.dump({"errors": [], "parcels_screened": 2}, f)
        out = os.path.join(tmp, "reports")
        manifest = B.build_reports(screen, STORE, out)
        self.assertEqual(manifest["reports"], 2)
        self.assertEqual(manifest["counts"], {"scheme": 1, "no_schemes": 1, "error": 0})
        for pid in (SCHEME_PID, NOSCHEME_PID):
            self.assertTrue(os.path.isfile(os.path.join(out, pid + ".md")))
        self.assertTrue(os.path.isfile(os.path.join(out, "index.md")))
        with open(os.path.join(out, "index.md")) as f:
            idx = f.read()
        self.assertIn(SCHEME_PID, idx)
        self.assertIn(NOSCHEME_PID, idx)
        self.assertIn("no_schemes_generated", idx)

    def test_batch_error_parcels_get_error_reports(self):
        tmp = tempfile.mkdtemp(prefix="evid_batch_err_")
        screen = os.path.join(tmp, "screen")
        os.makedirs(screen)
        d = os.path.join(screen, "BADPID00000001")
        os.makedirs(d)
        rep = _load(NOSCHEME_PID)
        rep = dict(rep, parcel_id="BADPID00000001", status="error",
                   schemes=[], ranked_order=[],
                   error="RuntimeError: synthetic failure")
        with open(os.path.join(d, "report.json"), "w") as f:
            json.dump(rep, f)
        with open(os.path.join(screen, "summary.json"), "w") as f:
            json.dump({"errors": [{"parcel_id": "BADPID00000001",
                                    "error": "RuntimeError: synthetic failure"}],
                       "parcels_screened": 0}, f)
        out = os.path.join(tmp, "reports")
        manifest = B.build_reports(screen, STORE, out)
        self.assertEqual(manifest["counts"]["error"], 1)
        with open(os.path.join(out, "BADPID00000001.md")) as f:
            md = f.read()
        self.assertIn("ERROR", md)
        self.assertIn("RuntimeError: synthetic failure", md)

    def test_index_carries_rg_verdict_basis(self):
        # The real scheme parcel (M-1, top verdict UNKNOWN, 6 applicable
        # rules) must read "evaluated"; a synthetic vacuous-PASS parcel
        # (PASS, 0 applicable rules) must read "no_applicable_rules"; the
        # no-scheme parcel gets an empty basis cell.
        tmp = tempfile.mkdtemp(prefix="evid_batch_basis_")
        screen = os.path.join(tmp, "screen")
        os.makedirs(screen)
        vac_pid = "VACUOUS00000001"
        for pid in (SCHEME_PID, NOSCHEME_PID):
            d = os.path.join(screen, pid)
            os.makedirs(d)
            shutil.copy(os.path.join(SCREEN, pid, "report.json"),
                        os.path.join(d, "report.json"))
        rep = _load(SCHEME_PID)
        rep = json.loads(json.dumps(rep))  # deep copy
        rep["parcel_id"] = vac_pid
        smap = {s["scheme_id"]: s for s in rep["schemes"]}
        top = smap[rep["ranked_order"][0]]
        top["rulegraph_verdict"] = "PASS"
        top["rulegraph_applicable_rules"] = 0
        d = os.path.join(screen, vac_pid)
        os.makedirs(d)
        with open(os.path.join(d, "report.json"), "w") as f:
            json.dump(rep, f)
        with open(os.path.join(screen, "summary.json"), "w") as f:
            json.dump({"errors": [], "parcels_screened": 3}, f)
        out = os.path.join(tmp, "reports")
        manifest = B.build_reports(screen, STORE, out)
        self.assertEqual(manifest["reports"], 3)
        with open(os.path.join(out, "index.md")) as f:
            lines = [ln for ln in f.read().splitlines()
                     if ln.startswith("| [`")]
        self.assertEqual(len(lines), 3)
        by_pid = {}
        for ln in lines:
            for pid in (SCHEME_PID, NOSCHEME_PID, vac_pid):
                if pid in ln:
                    by_pid[pid] = ln
        self.assertEqual(len(by_pid), 3)
        self.assertIn("| UNKNOWN | evaluated |", by_pid[SCHEME_PID])
        self.assertIn("| PASS | no_applicable_rules |", by_pid[vac_pid])
        # No-scheme parcel: rg verdict n/a, basis empty.
        cells = [c.strip() for c in by_pid[NOSCHEME_PID].split("|")]
        self.assertEqual(cells[6], "n/a")   # rg verdict
        self.assertEqual(cells[7], "")      # rg basis


if __name__ == "__main__":
    unittest.main(verbosity=2)
