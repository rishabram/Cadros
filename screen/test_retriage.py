"""Tests for screen.retriage (UNKNOWN re-triage on demand).

The script must recompute the blocker map from report.json files alone,
deterministically, and append analyst notes verbatim without editing them.
"""
import json
import os
import tempfile
import unittest

from .retriage import aggregate, render, retriage

STORE = {
    "rules": {
        "M-1-01": {"rule_id": "M-1-01", "_caddy_rule_name": "Min lot area"},
        "M-1-02": {"rule_id": "M-1-02", "_caddy_rule_name": "Min yards"},
        "MU-11-11": {"rule_id": "MU-11-11", "_caddy_rule_name": "No min lot size"},
    }
}


def _scheme(sid, verdict, applicable, rules):
    return {
        "scheme_id": sid,
        "rulegraph_verdict": verdict,
        "rulegraph_applicable_rules": applicable,
        "rulegraph": rules,
    }


def _rule(rid, outcome, reason=""):
    return {"rule_id": rid, "outcome": outcome, "applicable": True,
            "reason": reason}


def _parcel(pid, district, schemes):
    return {
        "parcel_id": pid,
        "status": "ok",
        "zoning": {"district": district},
        "schemes": schemes,
        "ranked_order": [s["scheme_id"] for s in schemes],
    }


class TestRetriage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        p1 = _parcel("P1", "M-1", [
            _scheme("s0", "UNKNOWN", 2, [
                _rule("M-1-01", "UNKNOWN", "no evaluator registered for None"),
                _rule("M-1-02", "UNKNOWN", "front setback value is unknown"),
            ]),
        ])
        p2 = _parcel("P2", "RMF-30", [
            _scheme("s0", "PASS", 0, [
                _rule("M-1-01", "PASS", "district scoped out"),
            ]),
        ])
        # fix: the vacuous scheme's rule must be non-applicable to count as vacuous
        p2["schemes"][0]["rulegraph"][0]["applicable"] = False
        for pid, parcel in (("P1", p1), ("P2", p2)):
            d = os.path.join(self.tmp, pid)
            os.makedirs(d)
            with open(os.path.join(d, "report.json"), "w") as f:
                json.dump(parcel, f)

    def test_aggregates(self):
        agg = aggregate(self.tmp, STORE)
        self.assertEqual(agg["n_schemes"], 2)
        self.assertEqual(agg["scheme_verdicts"]["UNKNOWN"], 1)
        self.assertEqual(agg["scheme_verdicts"]["PASS"], 1)
        self.assertEqual(agg["vacuous"]["RMF-30"], 1)
        self.assertEqual(
            agg["rule_outcomes"]["M-1"]["M-1-01"]["UNKNOWN"], 1)

    def test_blocker_classes(self):
        text = render(aggregate(self.tmp, STORE), "testscreen", "fp123")
        self.assertIn("stored-but-not-executable", text)
        self.assertIn("context gap (needs site/building facts)", text)
        self.assertIn("`M-1-01` (Min lot area)", text)
        self.assertIn("`M-1-02` (Min yards)", text)
        self.assertIn("**1** UNKNOWN / **0** FAIL / **0** MANUAL_REVIEW / "
                        "**0** CONDITIONAL_PASS / **1** PASS", text)
        self.assertIn("RMF-30 ×1", text)

    def test_notes_appended_verbatim(self):
        notes = os.path.join(self.tmp, "notes.md")
        with open(notes, "w") as f:
            f.write("# analyst notes\n\nkeep me  \n")
        store = os.path.join(self.tmp, "store.json")
        with open(store, "w") as f:
            json.dump(STORE, f)
        out, _ = retriage(self.tmp, store, notes_path=notes)
        with open(out) as f:
            text = f.read()
        self.assertIn("# analyst notes\n\nkeep me\n", text)
        self.assertIn("## Headline", text)

    def test_missing_notes_gets_placeholder(self):
        store = os.path.join(self.tmp, "store.json")
        with open(store, "w") as f:
            json.dump(STORE, f)
        out, _ = retriage(self.tmp, store,
                          notes_path=os.path.join(self.tmp, "nope.md"))
        with open(out) as f:
            self.assertIn("No analyst notes file found", f.read())

    def test_deterministic(self):
        store = os.path.join(self.tmp, "store.json")
        with open(store, "w") as f:
            json.dump(STORE, f)
        out1, _ = retriage(self.tmp, store)
        with open(out1) as f:
            t1 = f.read()
        out2, _ = retriage(self.tmp, store)
        with open(out2) as f:
            self.assertEqual(f.read(), t1)


if __name__ == "__main__":
    unittest.main()
