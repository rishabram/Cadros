"""Pins the quote-fidelity pass over Caddy's 51 rules.

If any store quote changes, or any rule is added/removed, this test fails
loudly and the quote-fidelity wave must be re-run by a human-eyed pass --
never auto-reclassified. See QUOTE_FIDELITY.md and
rulegraph/quote_fidelity.py.
"""

import unittest

from rulegraph.quote_fidelity import (
    CADDY_RULE_COUNT,
    EXPECTED_COUNTS,
    MANUAL,
    classify,
    counts,
)


class TestQuoteFidelityPins(unittest.TestCase):
    def test_caddy_rule_count(self):
        results = classify()
        self.assertEqual(
            len(results), CADDY_RULE_COUNT,
            f"expected {CADDY_RULE_COUNT} Caddy rules (59 minus Rishab's 8), "
            f"got {len(results)} -- store membership changed, re-run the pass",
        )

    def test_classification_counts(self):
        tally = counts(classify())
        self.assertEqual(
            tally, EXPECTED_COUNTS,
            f"classification counts moved: {tally} vs pinned {EXPECTED_COUNTS} "
            f"-- re-run the quote-fidelity wave",
        )

    def test_no_unclassified_or_changed_quotes(self):
        # classify() marks any verifiable-but-unjudged rule or any
        # changed-since-the-pass quote as MISMATCH; the pinned count is 0.
        bad = [r for r in classify() if r["category"] == "MISMATCH"]
        self.assertEqual(
            bad, [],
            "MISMATCH rows appeared (changed quotes or unjudged rules): "
            + "; ".join(f"{r['rule_id']}: {r['detail']}" for r in bad),
        )

    def test_manual_table_covers_every_verifiable_rule(self):
        # Every non-corpus-gap Caddy rule must have a manual judgment;
        # otherwise classify() would emit MISMATCH and the counts test fails.
        # This test names the coverage explicitly for readability.
        self.assertEqual(len(MANUAL), 19)
        self.assertEqual(
            sum(1 for c, _, _ in MANUAL.values() if c == "VERBATIM"), 4)
        self.assertEqual(
            sum(1 for c, _, _ in MANUAL.values() if c == "VALUE_MATCH"), 15)

    def test_corpus_gap_rules_name_missing_sections(self):
        gaps = [r for r in classify() if r["category"] == "CORPUS_GAP"]
        self.assertEqual(len(gaps), 32)
        sections = {r["citation"].split(" ")[0] for r in gaps}
        self.assertEqual(sections, {"21A.25.040", "21A.25.050"})


if __name__ == "__main__":
    unittest.main()
