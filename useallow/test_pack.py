"""Tests for the use-allow pack parser (useallow/pack.py).

Parses the real source file at
~/workspace/neron-zoning/21A33_candidates_M1_OS_PL.md and asserts
counts, verdicts, status/footnote/flag parsing rules, fingerprint
stability + pin, and that sections 4+ are never parsed.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from useallow.pack import (
    PINNED_PACK_FINGERPRINT,
    UsePack,
    UseRow,
    load_pack,
)

WANT_HV = {"result": "VERIFIED", "verified_by": "Rohan", "verified_on": "2026-09-23"}


class TestUsePack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = load_pack()
        cls.by_id = {r.rule_id: r for r in cls.pack.rows}

    def test_counts_per_district(self):
        counts = {}
        for r in self.pack.rows:
            counts[r.district] = counts.get(r.district, 0) + 1
        self.assertEqual(counts.get("M-1"), 122)
        self.assertEqual(counts.get("OS"), 27)
        self.assertEqual(counts.get("PL"), 42)
        self.assertEqual(len(self.pack.rows), 191)

    def test_status_tallies_match_source_doc(self):
        # The source doc's own tallies: M-1 98/17/6/1; OS 24/2/0/1; PL 40/2/0/0.
        got = {}
        for r in self.pack.rows:
            got[(r.district, r.status)] = got.get((r.district, r.status), 0) + 1
        self.assertEqual(
            got,
            {
                ("M-1", "permitted"): 98,
                ("M-1", "conditional"): 17,
                ("M-1", "not_permitted"): 6,
                ("M-1", "unresolved"): 1,
                ("OS", "permitted"): 24,
                ("OS", "conditional"): 2,
                ("OS", "unresolved"): 1,
                ("PL", "permitted"): 40,
                ("PL", "conditional"): 2,
            },
        )

    def test_all_rows_human_verified(self):
        for r in self.pack.rows:
            self.assertIsNotNone(r.human_verification, r.rule_id)
            self.assertEqual(r.human_verification, WANT_HV, r.rule_id)

    def test_m1_u28_unresolved_with_flags(self):
        r = self.by_id["M1-U-28"]
        self.assertEqual(r.status, "unresolved")
        self.assertTrue(r.flags, "unresolved row must carry flags")
        self.assertIn("UNRESOLVED", r.flags)

    def test_os_u27_unresolved(self):
        self.assertEqual(self.by_id["OS-U-27"].status, "unresolved")

    def test_footnote_parsing(self):
        self.assertEqual(self.by_id["M1-U-01"].footnotes, [21])
        self.assertEqual(self.by_id["M1-U-03"].footnotes, [6, 10])
        self.assertEqual(self.by_id["M1-U-20"].footnotes, [18, 19])
        self.assertEqual(self.by_id["M1-U-34"].footnotes, [12, 13, 19])
        self.assertEqual(self.by_id["M1-U-104"].footnotes, [12, 22])
        self.assertEqual(self.by_id["M1-U-13"].footnotes, [])  # "Conditional (C)"
        self.assertEqual(self.by_id["M1-U-02"].footnotes, [])  # "Permitted"

    def test_fingerprint_stable_across_reloads(self):
        self.assertEqual(load_pack().fingerprint, self.pack.fingerprint)

    def test_fingerprint_pinned(self):
        self.assertTrue(PINNED_PACK_FINGERPRINT, "pin must be set")
        self.assertEqual(self.pack.fingerprint, PINNED_PACK_FINGERPRINT)

    def test_not_permitted_rows_exist(self):
        for rid in ("M1-U-29", "M1-U-41", "M1-U-51"):
            self.assertEqual(self.by_id[rid].status, "not_permitted", rid)

    def test_section4_plus_not_parsed(self):
        # Exactly the 191 candidate IDs from sections 1-3, nothing from later
        # sections (which only discuss footnote fragments / prose).
        expected = (
            {f"M1-U-{n:02d}" for n in range(1, 123)}
            | {f"OS-U-{n:02d}" for n in range(1, 28)}
            | {f"PL-U-{n:02d}" for n in range(1, 43)}
        )
        ids = [r.rule_id for r in self.pack.rows]
        self.assertEqual(set(ids), expected)
        self.assertEqual(len(ids), len(set(ids)), "duplicate rule ids")

    def test_interface_shape(self):
        r = self.by_id["M1-U-01"]
        self.assertIsInstance(r, UseRow)
        self.assertIsInstance(self.pack, UsePack)
        self.assertIsInstance(r.footnotes, list)
        self.assertEqual(r.district, "M-1")
        self.assertEqual(r.marking, "P 21 / P 21 / P")

    def test_missing_file_is_loud(self):
        with self.assertRaises(FileNotFoundError):
            load_pack("/nonexistent/path/use_pack.md")


if __name__ == "__main__":
    unittest.main()
