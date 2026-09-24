"""Tests for useallow.mu_pack (Caddy's verified_uses_mu.json -> 322 UseRows).

Run: venv/bin/python -m unittest useallow.test_mu_pack -v
"""
import unittest

from .mu_pack import (
    DEFAULT_MU_PATH,
    PINNED_MU_PACK_FINGERPRINT,
    load_mu_pack,
)


class TestMuPack(unittest.TestCase):
    def setUp(self):
        self.pack = load_mu_pack()

    def test_322_rows(self):
        self.assertEqual(len(self.pack.rows), 322)

    def test_per_district_counts(self):
        counts = {}
        for r in self.pack.rows:
            counts[r.district] = counts.get(r.district, 0) + 1
        self.assertEqual(counts, {"MU-5": 106, "MU-6": 105, "MU-11": 111})

    def test_status_counts_match_source_tallies(self):
        from collections import Counter

        per_dist_status = Counter((r.district, r.status) for r in self.pack.rows)
        self.assertEqual(per_dist_status[("MU-5", "permitted")], 95)
        self.assertEqual(per_dist_status[("MU-5", "conditional")], 11)
        self.assertEqual(per_dist_status[("MU-6", "permitted")], 100)
        self.assertEqual(per_dist_status[("MU-6", "conditional")], 5)
        self.assertEqual(per_dist_status[("MU-11", "permitted")], 102)
        self.assertEqual(per_dist_status[("MU-11", "conditional")], 9)

    def test_ids_deterministic_and_district_prefixed(self):
        self.assertEqual(self.pack.rows[0].rule_id, "MU5-U-001")
        self.assertEqual(self.pack.rows[105].rule_id, "MU5-U-106")
        self.assertEqual(self.pack.rows[106].rule_id, "MU6-U-001")
        self.assertEqual(self.pack.rows[210].rule_id, "MU6-U-105")
        self.assertEqual(self.pack.rows[211].rule_id, "MU11-U-001")
        self.assertEqual(self.pack.rows[321].rule_id, "MU11-U-111")
        ids = [r.rule_id for r in self.pack.rows]
        self.assertEqual(len(set(ids)), len(ids))

    def test_batch_human_verification_on_every_row(self):
        for r in self.pack.rows:
            hv = r.human_verification
            self.assertEqual(hv["result"], "VERIFIED")
            self.assertEqual(hv["verified_by"], "Rohan")
            self.assertEqual(hv["verified_on"], "2026-09-23")
            self.assertEqual(r.provenance, "caddy-batch-verified")

    def test_marking_status_agreement(self):
        for r in self.pack.rows:
            self.assertIn(
                (r.marking, r.status),
                (("P", "permitted"), ("C", "conditional")),
            )

    def test_no_footnote_rows(self):
        # The source names carry no footnote markers; none should route to
        # MANUAL_REVIEW from this pack.
        for r in self.pack.rows:
            self.assertEqual(r.footnotes, [])

    def test_fingerprint_pinned(self):
        self.assertEqual(
            self.pack.fingerprint, PINNED_MU_PACK_FINGERPRINT
        )

    def test_missing_file_raises_loud(self):
        with self.assertRaises(FileNotFoundError):
            load_mu_pack("/nonexistent/verified_uses_mu.json")

    def test_default_path_is_caddy_drop(self):
        self.assertIn("caddy_drop", DEFAULT_MU_PATH)
        self.assertTrue(DEFAULT_MU_PATH.endswith("verified_uses_mu.json"))


class TestFootnoteMarkerExtraction(unittest.TestCase):
    """The programmatic footnote-marker check the module docstring promises.

    Audit round 2 found the docstring claimed this check at load but no code
    existed — these tests pin the behavior, marker forms and all.
    """

    def test_superscript_digits(self):
        from .mu_pack import _extract_footnote_markers

        name, notes = _extract_footnote_markers("Retail¹")
        self.assertEqual(notes, [1])
        self.assertEqual(name, "Retail")
        name, notes = _extract_footnote_markers("Theater¹²")
        self.assertEqual(notes, [12])
        self.assertEqual(name, "Theater")

    def test_parenthesized_digit_groups(self):
        from .mu_pack import _extract_footnote_markers

        name, notes = _extract_footnote_markers("Clinic (medical, dental) (1, 2)")
        self.assertEqual(notes, [1, 2])
        self.assertEqual(name, "Clinic (medical, dental)")
        # Parenthetical WORDS are not markers.
        name, notes = _extract_footnote_markers("Assisted living facility (large)")
        self.assertEqual(notes, [])
        self.assertEqual(name, "Assisted living facility (large)")

    def test_bracketed_and_trailing_digits(self):
        from .mu_pack import _extract_footnote_markers

        name, notes = _extract_footnote_markers("Store [3]")
        self.assertEqual(notes, [3])
        self.assertEqual(name, "Store")
        name, notes = _extract_footnote_markers("Pawnshop2")
        self.assertEqual(notes, [2])
        self.assertEqual(name, "Pawnshop")

    def test_clean_names_pass_through_unchanged(self):
        from .mu_pack import _extract_footnote_markers

        for raw in ("Rooming (boarding) house", "Retail (goods or services)",
                    "Single-family (detached)", "Automobile repair (major)"):
            name, notes = _extract_footnote_markers(raw)
            self.assertEqual(notes, [])
            self.assertEqual(name, raw)

    def test_letter_prefixed_markers(self):
        # The corpus's own (P/C##) notation: P/C is the table's
        # permitted/conditional column marker — dropped; digits become
        # footnotes. Extends the marker audit's false-negative class.
        from .mu_pack import _extract_footnote_markers

        name, notes = _extract_footnote_markers("Brewpub (P6,10)")
        self.assertEqual(notes, [6, 10])
        self.assertEqual(name, "Brewpub")
        name, notes = _extract_footnote_markers("Accessory use (P21)")
        self.assertEqual(notes, [21])
        self.assertEqual(name, "Accessory use")
        name, notes = _extract_footnote_markers("Shop (C2)")
        self.assertEqual(notes, [2])
        self.assertEqual(name, "Shop")
        # Coexists with parenthetical words — the words survive.
        name, notes = _extract_footnote_markers("Clinic (medical, dental) (P6)")
        self.assertEqual(notes, [6])
        self.assertEqual(name, "Clinic (medical, dental)")
        # Narrow by design: lowercase and non-P/C letters are NOT stripped
        # (false negative = safe direction; name passes through clean).
        name, notes = _extract_footnote_markers("Bakery (p6)")
        self.assertEqual(notes, [])
        self.assertEqual(name, "Bakery (p6)")
        name, notes = _extract_footnote_markers("Accessory unit (ADU)")
        self.assertEqual(notes, [])
        self.assertEqual(name, "Accessory unit (ADU)")

    def test_real_digit_bearing_names_untouched(self):
        # Name-safety review (MARKER_AUDIT.md §5): the ONLY digit-bearing
        # names in the 322-name source are mid-name hyphenated K-12 —
        # never letter-prefixed marker candidates.
        from .mu_pack import _extract_footnote_markers

        for raw in ("K-12 Private", "K-12 Public"):
            name, notes = _extract_footnote_markers(raw)
            self.assertEqual(notes, [])
            self.assertEqual(name, raw)

    def test_all_322_source_names_marker_free(self):
        # The extended pattern changes nothing on the real source: 0
        # occurrences of any marker form, so the fingerprint pin holds.
        import json

        from .mu_pack import DEFAULT_MU_PATH, _extract_footnote_markers

        with open(DEFAULT_MU_PATH, encoding="utf-8") as fh:
            doc = json.load(fh)
        count = 0
        for district in ("MU-5", "MU-6", "MU-11"):
            for block in ("permitted", "conditional"):
                for raw in doc["districts"][district][block]:
                    count += 1
                    name, notes = _extract_footnote_markers(raw.strip())
                    self.assertEqual(notes, [], f"marker found in {raw!r}")
                    self.assertEqual(name, raw.strip())
        self.assertEqual(count, 322)

    def test_marked_row_routes_to_manual_review(self):
        # End-to-end: a marked name in the source becomes a row with
        # footnotes, and the engine routes it to MANUAL_REVIEW — never
        # silently dropped, never evaluated.
        import json
        import os
        import tempfile

        from .engine import evaluate_uses
        from .mu_pack import load_mu_pack

        doc = {
            "source": {"human_verified_by": "Rohan", "human_verified_on": "2026-09-23"},
            "districts": {
                "MU-5": {"permitted": ["Bakery¹"], "conditional": []},
                "MU-6": {"permitted": [], "conditional": []},
                "MU-11": {"permitted": [], "conditional": []},
            },
        }
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False
        ) as fh:
            json.dump(doc, fh)
            tmp = fh.name
        try:
            pack = load_mu_pack(tmp)
        finally:
            os.unlink(tmp)
        self.assertEqual(len(pack.rows), 1)
        row = pack.rows[0]
        self.assertEqual(row.footnotes, [1])
        self.assertEqual(row.use_name, "Bakery")
        result = evaluate_uses("MU-5", ["Bakery"], pack)
        self.assertEqual(result["verdict"], "MANUAL_REVIEW")
        self.assertEqual(result["per_use"][0]["verdict"], "MANUAL_REVIEW")

    def test_letter_prefixed_marked_row_routes_to_manual_review(self):
        # End-to-end for the corpus's own notation: a future prose-rendered
        # source carrying "(P6,10)" parses into footnotes and the engine
        # routes the row to MANUAL_REVIEW — never silently dropped, never
        # evaluated.
        import json
        import os
        import tempfile

        from .engine import evaluate_uses
        from .mu_pack import load_mu_pack

        doc = {
            "source": {"human_verified_by": "Rohan", "human_verified_on": "2026-09-23"},
            "districts": {
                "MU-5": {"permitted": ["Brewpub (P6,10)"], "conditional": []},
                "MU-6": {"permitted": [], "conditional": []},
                "MU-11": {"permitted": [], "conditional": []},
            },
        }
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False
        ) as fh:
            json.dump(doc, fh)
            tmp = fh.name
        try:
            pack = load_mu_pack(tmp)
        finally:
            os.unlink(tmp)
        self.assertEqual(len(pack.rows), 1)
        row = pack.rows[0]
        self.assertEqual(row.footnotes, [6, 10])
        self.assertEqual(row.use_name, "Brewpub")
        result = evaluate_uses("MU-5", ["Brewpub"], pack)
        self.assertEqual(result["verdict"], "MANUAL_REVIEW")
        self.assertEqual(result["per_use"][0]["verdict"], "MANUAL_REVIEW")


if __name__ == "__main__":
    unittest.main()
