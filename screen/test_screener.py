#!/usr/bin/env python3
"""Unit tests for the mass screener (screen/screener.py).

Run:  ./venv/bin/python -m unittest screen.test_screener -v
from the neron-scratch root. Uses only temp dirs — demo/Jefferson baselines
and goldens are never touched.
"""
from __future__ import annotations

import csv
import json
import os
import statistics
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from screen.screener import CSV_COLUMNS, screen_manifest  # noqa: E402

MU11_ZONING = {
    "min_frontage_ft": 50,
    "min_lot_area_sqft": 5000,
    "road_width_ft": 55,
    "district": "MU-11",
    "zone_label": "MU-11 (SYNTHETIC test)",
    "source": "SYNTHETIC test fixture",
}
MU11_FINANCE = {
    "sale_price_per_lot": 95000,
    "road_cost_per_lf": 500,
    "soft_costs_fixed": 120000,
    "contingency_pct": 0.10,
    "source": "SYNTHETIC test fixture",
}


def rect_feature(parcel_id, w, h):
    return {
        "type": "Feature",
        "geometry": {"type": "Polygon",
                     "coordinates": [[[0, 0], [w, 0], [w, h], [0, h], [0, 0]]]},
        "properties": {"parcel_id": parcel_id, "crs": "local-feet",
                       "source": "SYNTHETIC test fixture"},
    }


def write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f)


class ScreenerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.manifest_dir = os.path.join(self.tmp.name, "m")
        os.makedirs(self.manifest_dir)

    def _manifest(self, parcels, **kw):
        doc = {"screen_name": "test", "max_schemes": 2, "parcels": parcels,
               **kw}
        p = os.path.join(self.manifest_dir, "manifest.json")
        write_json(p, doc)
        return p

    def _parcel_entry(self, parcel_id, w=420, h=320, zoning=None,
                      finance=None, program=None, as_files=False):
        entry = {"parcel_id": parcel_id}
        gj = rect_feature(parcel_id, w, h)
        z = dict(MU11_ZONING if zoning is None else zoning)
        f = dict(MU11_FINANCE if finance is None else finance)
        if as_files:
            for name, obj in (("parcel.geojson", gj), ("zoning.json", z),
                              ("finance.json", f)):
                fp = os.path.join(self.manifest_dir, f"{parcel_id}.{name}")
                write_json(fp, obj)
                entry[{"parcel.geojson": "parcel_geojson",
                       "zoning.json": "zoning_config",
                       "finance.json": "finance_config"}[name]] = \
                    os.path.basename(fp)
            if program is not None:
                fp = os.path.join(self.manifest_dir, f"{parcel_id}.program.json")
                write_json(fp, program)
                entry["program"] = os.path.basename(fp)
        else:
            entry["parcel_geojson"] = gj
            entry["zoning_config"] = z
            entry["finance_config"] = f
            if program is not None:
                entry["program"] = program
        return entry

    def _run(self, manifest_path, out_name="out"):
        out = os.path.join(self.tmp.name, out_name)
        rows, summary = screen_manifest(manifest_path, out_root=out)
        return rows, summary, out

    def _csv_rows(self, out):
        with open(os.path.join(out, "screening_results.csv")) as f:
            r = csv.DictReader(f)
            self.assertEqual(r.fieldnames, CSV_COLUMNS)
            return list(r)

    # --- tests ---------------------------------------------------------

    def test_csv_schema_columns(self):
        mp = self._manifest([self._parcel_entry("p1")])
        _, _, out = self._run(mp)
        rows = self._csv_rows(out)
        self.assertTrue(any(r["row_kind"] == "scheme" for r in rows))
        s = next(r for r in rows if r["row_kind"] == "scheme")
        self.assertEqual(s["parcel_id"], "p1")
        self.assertEqual(s["district"], "MU-11")
        self.assertTrue(s["zone_label"].startswith("MU-11"))
        self.assertTrue(int(s["lots"]) >= 4)
        self.assertIn(s["rg_verdict"],
                      ("PASS", "CONDITIONAL_PASS", "FAIL", "UNKNOWN",
                       "MANUAL_REVIEW", ""))
        self.assertIn(s["geometry_clean"], ("true", "false"))
        # per-rule counts are non-negative ints that sum to rules evaluated
        total = (int(s["rg_pass"]) + int(s["rg_conditional"])
                 + int(s["rg_fail"]) + int(s["rg_unknown"])
                 + int(s["rg_manual_review"]))
        self.assertGreater(total, 0)
        self.assertIn(s["use_verdict"],
                      ("PASS", "CONDITIONAL_PASS", "FAIL", "UNKNOWN",
                       "MANUAL_REVIEW", ""))
        self.assertGreaterEqual(int(s["unknowns_count"]), 0)

    def test_determinism_byte_identical(self):
        mp = self._manifest([
            self._parcel_entry("p1"),
            self._parcel_entry("p2", w=500, h=400, as_files=True),
        ])
        _, _, out1 = self._run(mp, "out1")
        _, _, out2 = self._run(mp, "out2")
        with open(os.path.join(out1, "screening_results.csv"), "rb") as a, \
                open(os.path.join(out2, "screening_results.csv"), "rb") as b:
            self.assertEqual(a.read(), b.read(),
                             "screening_results.csv differs between runs")
        # summary.json carries absolute run paths (csv, manifest); normalize
        # those two fields, everything else must be identical.
        def norm(out):
            with open(os.path.join(out, "summary.json")) as f:
                s = json.load(f)
            s["csv"] = "<csv>"
            s["manifest"] = "<manifest>"
            return s
        self.assertEqual(norm(out1), norm(out2),
                         "summary.json differs between runs")

    def test_error_row_never_skips(self):
        bad_gj = {"type": "Feature",
                  "geometry": {"type": "LineString",
                               "coordinates": [[0, 0], [10, 10]]},
                  "properties": {"parcel_id": "bad", "crs": "local-feet"}}
        bad_zoning = dict(MU11_ZONING)
        del bad_zoning["min_lot_area_sqft"]  # pipeline must fail loudly
        mp = self._manifest([
            {"parcel_id": "bad-geom", "parcel_geojson": bad_gj,
             "zoning_config": MU11_ZONING, "finance_config": MU11_FINANCE},
            {"parcel_id": "bad-zoning",
             "parcel_geojson": rect_feature("bad-zoning", 420, 320),
             "zoning_config": bad_zoning, "finance_config": MU11_FINANCE},
            self._parcel_entry("good"),
        ])
        rows, summary, out = self._run(mp)
        csv_rows = self._csv_rows(out)
        errs = [r for r in csv_rows if r["row_kind"] == "error"]
        self.assertEqual(len(errs), 2)
        for r in errs:
            self.assertTrue(r["error"], "error row must carry the message")
            self.assertEqual(r["scheme_id"], "")
        # the good parcel still screened — one failure never aborts the run
        self.assertTrue(any(r["parcel_id"] == "good" and
                            r["row_kind"] == "scheme" for r in csv_rows))
        self.assertEqual(summary["parcels_errored"], 2)
        self.assertEqual(summary["parcels_screened"], 1)
        self.assertEqual(len(summary["errors"]), 2)

    def test_no_schemes_row(self):
        # 60x40 = 2400 sqft < 5000 minimum -> no schemes possible
        mp = self._manifest([self._parcel_entry("tiny", w=60, h=40)])
        _, summary, out = self._run(mp)
        rows = self._csv_rows(out)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["row_kind"], "no_schemes")
        self.assertEqual(rows[0]["error"], "")
        self.assertEqual(summary["parcels_no_schemes"], 1)
        self.assertEqual(summary["scheme_rows"], 0)

    def test_summary_math(self):
        mp = self._manifest([
            self._parcel_entry("a", w=420, h=320),
            self._parcel_entry("b", w=600, h=500),
        ])
        _, summary, out = self._run(mp)
        rows = [r for r in self._csv_rows(out) if r["row_kind"] == "scheme"]
        profits = [float(r["profit"]) for r in rows]
        margins = [float(r["margin"]) for r in rows]
        self.assertEqual(summary["scheme_rows"], len(rows))
        self.assertAlmostEqual(summary["profit_mean"],
                               round(statistics.fmean(profits), 2))
        self.assertAlmostEqual(summary["profit_median"],
                               round(statistics.median(profits), 2))
        self.assertAlmostEqual(summary["margin_mean"],
                               round(statistics.fmean(margins), 4))
        self.assertAlmostEqual(summary["margin_median"],
                               round(statistics.median(margins), 4))
        self.assertEqual(summary["rulegraph_outcomes"]["PASS"],
                         sum(int(r["rg_pass"]) for r in rows))
        self.assertEqual(summary["rulegraph_outcomes"]["FAIL"],
                         sum(int(r["rg_fail"]) for r in rows))
        self.assertEqual(summary["rulegraph_outcomes"]["UNKNOWN"],
                         sum(int(r["rg_unknown"]) for r in rows))
        # top scheme per parcel is the first scheme row of each parcel
        seen = []
        for r in rows:
            if r["parcel_id"] not in seen:
                seen.append(r["parcel_id"])
        top_lots = sum(int(next(r["lots"] for r in rows
                                if r["parcel_id"] == pid)) for pid in seen)
        self.assertEqual(summary["total_lots_top_scheme"], top_lots)

    def test_unknowns_propagate_not_zeroed(self):
        # no program -> context attributes unknown -> UNKNOWN verdicts kept
        mp = self._manifest([self._parcel_entry("u1")])
        _, _, out = self._run(mp)
        rows = [r for r in self._csv_rows(out) if r["row_kind"] == "scheme"]
        self.assertTrue(any(int(r["rg_unknown"]) > 0 for r in rows))
        self.assertTrue(any(int(r["unknowns_count"]) > 0 for r in rows))
        # and they are NOT silently counted as passes
        for r in rows:
            rep = json.load(open(os.path.join(
                out, r["parcel_id"], "report.json")))
            gaps = rep["rulegraph"]["gaps"]
            self.assertEqual(int(r["unknowns_count"]), len(gaps))

    def test_vacuous_pass_labeling(self):
        # A district with no rules in the store (M-2) yields PASS with zero
        # applicable rules -> basis "no_applicable_rules". A covered district
        # (MU-11) yields basis "evaluated". The verdict enum itself is never
        # relabeled: both rows keep rg_verdict == "PASS".
        m2_zoning = dict(MU11_ZONING, district="M-2",
                         zone_label="M-2 (SYNTHETIC test)")
        mp = self._manifest([
            self._parcel_entry("m2p", zoning=m2_zoning),
            self._parcel_entry("mu11p"),
        ])
        _, summary, out = self._run(mp)
        srows = [r for r in self._csv_rows(out) if r["row_kind"] == "scheme"]
        by_parcel = {}
        for r in srows:
            by_parcel.setdefault(r["parcel_id"], []).append(r)
        self.assertIn("m2p", by_parcel)
        for m2 in by_parcel["m2p"]:
            self.assertEqual(m2["rg_verdict"], "PASS")
            self.assertEqual(m2["rg_applicable_rules"], "0")
            self.assertEqual(m2["rg_verdict_basis"], "no_applicable_rules")
        for mu11 in by_parcel["mu11p"]:
            self.assertGreater(int(mu11["rg_applicable_rules"]), 0)
            self.assertEqual(mu11["rg_verdict_basis"], "evaluated")
        vacuous_rows = [r for r in srows
                        if r["rg_verdict_basis"] == "no_applicable_rules"]
        self.assertTrue(len(vacuous_rows) >= 1)
        self.assertTrue(all(r["rg_verdict"] == "PASS" and
                            r["rg_applicable_rules"] == "0"
                            for r in vacuous_rows))
        self.assertEqual(summary["rg_vacuous_pass_schemes"], len(vacuous_rows))
        self.assertIn("no_applicable_rules",
                      summary["rg_verdict_basis_note"])

    def test_verdict_enum_unchanged_by_basis(self):
        # The qualifier is a separate field; no new verdict label may leak
        # into rg_verdict.
        mp = self._manifest([self._parcel_entry("e1")])
        _, _, out = self._run(mp)
        for r in self._csv_rows(out):
            self.assertIn(r["rg_verdict"],
                          ("PASS", "CONDITIONAL_PASS", "FAIL", "UNKNOWN",
                           "MANUAL_REVIEW", ""))
            self.assertIn(r["rg_verdict_basis"],
                          ("evaluated", "no_applicable_rules", ""))

    def test_inline_and_path_inputs_agree(self):
        prog = {"_note": "SYNTHETIC", "district": "MU-11"}
        mp = self._manifest([
            self._parcel_entry("inline", program=prog),
            self._parcel_entry("fromfile", as_files=True, program=prog),
        ])
        _, summary, out = self._run(mp)
        rows = self._csv_rows(out)
        kinds = {r["parcel_id"]: r["row_kind"] for r in rows
                 if r["row_kind"] == "scheme"}
        self.assertIn("inline", {r["parcel_id"] for r in rows})
        self.assertIn("fromfile", {r["parcel_id"] for r in rows})
        self.assertEqual(summary["parcels_errored"], 0)


if __name__ == "__main__":
    unittest.main()
