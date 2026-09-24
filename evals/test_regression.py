"""Tests for evals/regression.py — the automated regression harness.

Run: venv/bin/python -m unittest evals.test_regression -v (from the repo root)
"""
import json
import os
import unittest
from collections import Counter

from evals import regression as R

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestRegressionFastPath(unittest.TestCase):
    def test_fast_path_passes_with_zero_real_failures(self):
        report = R.run("fast")
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["real_failures"], 0)
        self.assertIn("fingerprints", report)
        self.assertIn("run_evals", report)
        self.assertEqual(report["run_evals"]["real_failures"], 0)

    def test_fingerprint_pins_agree_with_live_store(self):
        # The harness pins must match what the engine actually loads;
        # the unit-test suite pins the same values (rulegraph/test_rulegraph.py,
        # useallow/test_pack.py). A legitimate store change updates all three.
        report = {"checks": [], "findings": []}
        R.check_fingerprints(report)
        fails = [c for c in report["checks"] if c["status"] == "FAIL"]
        self.assertEqual(fails, [])

    def test_report_structure(self):
        report = R.run("fast")
        for key in ("mode", "checks", "findings", "fingerprints",
                    "run_evals", "real_failures", "verdict"):
            self.assertIn(key, report)


class TestVerdictFindings(unittest.TestCase):
    def test_verdict_change_is_finding_not_failure(self):
        # A compliance-verdict change must be reported as a finding and must
        # never become a check FAILURE (knowledge-pool rule).
        report = {"checks": [], "findings": []}
        observed = {
            "demo": {
                "rulegraph": Counter({"UNKNOWN": 7, "PASS": 1}),
                "use_allowance": Counter({"UNKNOWN": 8}),
            }
        }
        R.check_verdicts(report, observed)
        self.assertTrue(
            any("verdict change" in f for f in report["findings"]),
            f"expected a verdict-change finding, got {report['findings']}")
        fails = [c for c in report["checks"] if c["status"] == "FAIL"]
        self.assertEqual(fails, [])

    def test_verdict_pins_file_exists_after_full_run(self):
        self.assertTrue(os.path.exists(R.VERDICT_PINS_PATH))
        with open(R.VERDICT_PINS_PATH) as f:
            pins = json.load(f)
        self.assertIn("distributions", pins)
        self.assertIn("pinned_on", pins)


if __name__ == "__main__":
    unittest.main()
