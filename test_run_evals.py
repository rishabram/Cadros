"""run_evals.py exit-code policy: only by-design failures may exit 0.

Run: venv/bin/python -m unittest test_run_evals -v (from the repo root)

Policy under test (see run_evals.py docstring): the golden_bad_01 fixture is
adversarial — its "must FAIL" rows assert the validator flags known-bad
geometry, so a FAIL status there is by design. Anything else that FAILs is a
real failure. Exit 0 iff there are no real failures.
"""
import unittest

import run_evals as E


def row(case, metric, status):
    return (case, metric, "score", "target", status)


class TestIsByDesignFailure(unittest.TestCase):
    def test_adversarial_must_fail_row_is_by_design(self):
        self.assertTrue(E.is_by_design_failure(
            "golden_bad_01", "overlap_01: geom_no_overlap must FAIL"))

    def test_adversarial_control_row_is_not_by_design(self):
        # "must PASS" control rows pin the harness; a FAIL there is real.
        self.assertFalse(E.is_by_design_failure(
            "golden_bad_01", "clean_01 control: geom_no_overlap must PASS"))

    def test_other_case_never_by_design(self):
        self.assertFalse(E.is_by_design_failure(
            "golden_01", "top_scheme_profit must FAIL"))
        self.assertFalse(E.is_by_design_failure(
            "synthetic", "seeded_determinism must FAIL"))


class TestClassifyRows(unittest.TestCase):
    def test_current_suite_shape_has_no_real_failures(self):
        # Mirrors today's suite: 6 adversarial FAILs, everything else clean.
        rows = (
            [row("golden_01", "scheme_count", "PASS")] * 12
            + [row("golden_bad_01", f"bad_{i}: check_{i} must FAIL", "FAIL")
               for i in range(6)]
            + [row("golden_bad_01", "good_01 control: check must PASS", "PASS")]
            + [row("synthetic", "seeded_determinism", "PASS")]
            + [row("golden_01", "plan_classification", "N/A")] * 9
        )
        counts = E.classify_rows(rows)
        self.assertEqual(counts["passed"], 14)
        self.assertEqual(counts["by_design"], 6)
        self.assertEqual(counts["real_failures"], 0)
        self.assertEqual(counts["n_a"], 9)

    def test_must_fail_row_with_wrong_status_is_real(self):
        # The validator let bad geometry through: a genuine harness failure.
        rows = [row("golden_bad_01", "bad_01: check_01 must FAIL", "PASS")]
        self.assertEqual(E.classify_rows(rows)["real_failures"], 1)

    def test_control_row_fail_is_real(self):
        rows = [row("golden_bad_01", "good_01 control: check must PASS", "FAIL")]
        counts = E.classify_rows(rows)
        self.assertEqual(counts["real_failures"], 1)
        self.assertEqual(counts["by_design"], 0)

    def test_fail_outside_adversarial_fixture_is_real(self):
        rows = [row("golden_02", "top_scheme_profit", "FAIL")]
        self.assertEqual(E.classify_rows(rows)["real_failures"], 1)

    def test_empty_rows(self):
        self.assertEqual(
            E.classify_rows([]),
            {"passed": 0, "by_design": 0, "real_failures": 0, "n_a": 0},
        )


class TestExitPolicy(unittest.TestCase):
    """The exit decision is real_failures == 0, not total fails == 0."""

    def _exit_for(self, rows):
        return 1 if E.classify_rows(rows)["real_failures"] else 0

    def test_only_by_design_failures_exit_0(self):
        rows = [row("golden_bad_01", f"bad_{i}: c must FAIL", "FAIL")
                for i in range(6)]
        self.assertEqual(self._exit_for(rows), 0)

    def test_real_failure_exits_1(self):
        rows = [row("golden_bad_01", "bad_0: c must FAIL", "FAIL"),
                row("golden_01", "scheme_count", "FAIL")]
        self.assertEqual(self._exit_for(rows), 1)

    def test_all_pass_exits_0(self):
        self.assertEqual(self._exit_for([row("golden_01", "scheme_count", "PASS")]), 0)


if __name__ == "__main__":
    unittest.main()
