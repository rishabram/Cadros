"""Per-scheme building programs: split/merge helpers + pipeline wiring.

Run: venv/bin/python -m unittest prototype.test_pipeline_program -v
(from the repo root)
"""
import copy
import json
import tempfile
import unittest

from rulegraph import adapter as rg_adapter
from .pipeline import run_pipeline


def demo_program():
    with open("inputs/demo_program.json") as f:
        return json.load(f)


class TestSplitProgram(unittest.TestCase):
    def test_no_schemes_key_returns_program_unchanged(self):
        prog = demo_program()
        base, smap = rg_adapter.split_program(prog)
        self.assertEqual(smap, {})
        self.assertEqual(base, prog)
        self.assertNotIn("schemes", base)

    def test_schemes_key_popped_from_base(self):
        prog = {**demo_program(), "schemes": {"scheme_00": {"height_ft": 200}}}
        original = copy.deepcopy(prog)
        base, smap = rg_adapter.split_program(prog)
        self.assertNotIn("schemes", base)  # never reaches the typo guard
        self.assertEqual(smap, {"scheme_00": {"height_ft": 200}})
        self.assertEqual(prog, original)  # input dict not mutated
        # base keeps every non-schemes fact
        self.assertEqual(base["height_ft"], 38)

    def test_none_program(self):
        self.assertEqual(rg_adapter.split_program(None), (None, {}))

    def test_non_dict_schemes_raises(self):
        with self.assertRaises(ValueError):
            rg_adapter.split_program({"schemes": ["scheme_00"]})

    def test_non_dict_override_raises(self):
        with self.assertRaises(ValueError):
            rg_adapter.split_program({"schemes": {"scheme_00": 42}})

    def test_empty_schemes_map_is_no_override(self):
        base, smap = rg_adapter.split_program({**demo_program(), "schemes": {}})
        self.assertEqual(smap, {})
        self.assertNotIn("schemes", base)


class TestProgramForScheme(unittest.TestCase):
    def test_no_override_returns_base_unchanged(self):
        base = demo_program()
        out = rg_adapter.program_for_scheme(base, {}, "scheme_00")
        self.assertIs(out, base)  # same object: caller can share one context

    def test_override_merges_over_base(self):
        base = demo_program()
        smap = {"scheme_00": {"height_ft": 200, "abuts_zones_side": ["R-1"]}}
        out = rg_adapter.program_for_scheme(base, smap, "scheme_00")
        self.assertIsNot(out, base)
        self.assertEqual(out["height_ft"], 200)  # override wins
        self.assertEqual(out["abuts_zones_side"], ["R-1"])  # override adds
        self.assertEqual(out["building_form"], "row_house")  # base survives
        self.assertNotIn("schemes", out)
        self.assertEqual(base["height_ft"], 38)  # base not mutated

    def test_missing_scheme_gets_base(self):
        base = demo_program()
        smap = {"scheme_00": {"height_ft": 200}}
        self.assertIs(rg_adapter.program_for_scheme(base, smap, "scheme_07"), base)

    def test_none_base_with_override(self):
        out = rg_adapter.program_for_scheme(None, {"s1": {"height_ft": 80}}, "s1")
        self.assertEqual(out, {"height_ft": 80})

    def test_nested_schemes_key_stays_loud(self):
        # A "schemes" key inside an override is not a context attribute;
        # it must survive the merge so build_context() rejects it loudly.
        out = rg_adapter.program_for_scheme(
            demo_program(), {"s1": {"schemes": {}}}, "s1")
        self.assertIn("schemes", out)
        with self.assertRaises(ValueError):
            rg_adapter.build_context(program=out)


class TestPipelinePerScheme(unittest.TestCase):
    def _run(self, program):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return run_pipeline(
            "inputs/demo_parcel.geojson", "inputs/zoning.json",
            "inputs/finance.json", tmp.name, max_schemes=8,
            building_program=program,
        )["report"]

    def test_per_scheme_override_changes_one_scheme(self):
        report = self._run({
            # base: MU-11-01/02/03 PASS, MU-11-04 FAIL (demo rear 8 ft < 10 ft)
            **demo_program(),
            "schemes": {"scheme_00": {"height_ft": 200}},  # 200 ft -> MU-11-01 FAIL
        })
        rg = report["rulegraph"]
        self.assertTrue(rg["per_scheme_program"])
        verdicts = {s["scheme_id"]: s["rulegraph_verdict"] for s in report["schemes"]}
        by_id = {
            s["scheme_id"]: {r["rule_id"]: r for r in s["rulegraph"]}
            for s in report["schemes"]
        }
        # Every scheme fails MU-11-04 (demo rear setback 8 ft < 10 ft minimum).
        for sid in verdicts:
            self.assertEqual(by_id[sid]["MU-11-04"]["outcome"], "FAIL", sid)
        # The height override changes only scheme_00: MU-11-01 fails there alone.
        self.assertEqual(by_id["scheme_00"]["MU-11-01"]["outcome"], "FAIL")
        for sid, v in verdicts.items():
            if sid != "scheme_00":
                self.assertEqual(by_id[sid]["MU-11-01"]["outcome"], "PASS", sid)
        # per-scheme provenance is keyed by scheme id
        self.assertEqual(
            set(rg["context_provenance"]), set(verdicts))
        self.assertEqual(
            rg["context_provenance"]["scheme_00"]["height_ft"]["state"], "known")

    def test_per_scheme_facts_from_empty_base(self):
        # Base supplies only the district; one scheme gets height facts.
        report = self._run({
            "district": "MU-11",
            "schemes": {"scheme_03": {"height_ft": 80}},
        })
        by_id = {
            s["scheme_id"]: {r["rule_id"]: r for r in s["rulegraph"]}
            for s in report["schemes"]
        }
        self.assertEqual(by_id["scheme_03"]["MU-11-06"]["outcome"], "PASS")
        self.assertEqual(by_id["scheme_00"]["MU-11-06"]["outcome"], "UNKNOWN")

    def test_no_schemes_key_is_backward_compatible(self):
        report = self._run(demo_program())
        rg = report["rulegraph"]
        self.assertNotIn("per_scheme_program", rg)  # shape unchanged
        verdicts = {s["scheme_id"]: s["rulegraph_verdict"] for s in report["schemes"]}
        # Caddy extraction v2 made MU-11-01..04 executable: the demo program's
        # 8 ft rear setback honestly FAILs MU-11-04's 10 ft minimum on every
        # scheme (MU-11-01/02/03 PASS, MU-OPENSPACE-01 stays UNKNOWN).
        self.assertTrue(all(v == "FAIL" for v in verdicts.values()))
        by_id = {
            s["scheme_id"]: {r["rule_id"]: r for r in s["rulegraph"]}
            for s in report["schemes"]
        }
        self.assertEqual(by_id["scheme_00"]["MU-11-01"]["outcome"], "PASS")
        self.assertEqual(by_id["scheme_00"]["MU-11-04"]["outcome"], "FAIL")
        self.assertEqual(by_id["scheme_00"]["MU-OPENSPACE-01"]["outcome"], "UNKNOWN")
        # single flat provenance map, as before
        self.assertIn("height_ft", rg["context_provenance"])
        self.assertNotIn("scheme_00", rg["context_provenance"])

    def test_no_program_still_all_unknown(self):
        report = self._run(None)
        rg = report["rulegraph"]
        self.assertFalse(rg["program_supplied"])
        self.assertNotIn("per_scheme_program", rg)
        verdicts = {s["scheme_id"]: s["rulegraph_verdict"] for s in report["schemes"]}
        self.assertTrue(all(v == "UNKNOWN" for v in verdicts.values()))


if __name__ == "__main__":
    unittest.main()
