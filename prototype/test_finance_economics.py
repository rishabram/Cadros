"""Economics grounding: finance validation, --economics mapping, tagging schema.

Run: venv/bin/python -m unittest prototype.test_finance_economics -v
(from the repo root)
"""
import copy
import json
import unittest

from . import economics as econ_mod
from . import finance as finance_mod
from .__main__ import build_parser
from .schema import Lot, Road, Scheme

ECON_PATH = "inputs/economics_slco_2026.json"


def load_econ():
    with open(ECON_PATH) as f:
        return json.load(f)


def tiny_scheme():
    lot = Lot(lot_id="L1", polygon=[[0, 0], [70, 0], [70, 114], [0, 114]],
              area_sqft=8000.0, frontage_ft=70.0)
    road = Road(road_id="R1", centerline=[[0, 0], [0, 200]],
                width_ft=55.0, length_ft=200.0)
    return Scheme(scheme_id="s", parcel_id="p", lots=[lot], roads=[road])


class TestFinanceValidationStillLoud(unittest.TestCase):
    def test_missing_each_required_key_raises(self):
        base = {"sale_price_per_lot": 95000, "road_cost_per_lf": 500,
                "soft_costs_fixed": 120000}
        for key in ("sale_price_per_lot", "road_cost_per_lf", "soft_costs_fixed"):
            cfg = {k: v for k, v in base.items() if k != key}
            with self.assertRaises(ValueError, msg=f"missing {key}"):
                finance_mod.run_proforma(tiny_scheme(), cfg)

    def test_negative_values_raise(self):
        base = {"sale_price_per_lot": 95000, "road_cost_per_lf": 500,
                "soft_costs_fixed": 120000, "contingency_pct": 0.1}
        for key in base:
            cfg = dict(base, **{key: -1})
            with self.assertRaises(ValueError, msg=f"negative {key}"):
                finance_mod.run_proforma(tiny_scheme(), cfg)

    def test_mapped_config_flows_through_proforma(self):
        econ = load_econ()
        cfg = econ_mod.finance_config_from_economics(econ, "MU-11 test",
                                                     econ_path=ECON_PATH)
        pf = finance_mod.run_proforma(tiny_scheme(), cfg)
        self.assertEqual(pf.lot_count, 1)
        self.assertEqual(pf.revenue, 150000.0)  # MU-11 midpoint
        self.assertIn("economics_slco_2026.json", pf.assumptions["source"])


class TestDistrictMatching(unittest.TestCase):
    def test_mu11_label_matches_mu11(self):
        dkey, fallback = econ_mod.match_district(
            "MU-11 Mixed Use (test)", {"MU-11": {}, "M-1": {}, "DEFAULT": {}})
        self.assertEqual(dkey, "MU-11")
        self.assertFalse(fallback)

    def test_m1_label_matches_m1_not_mu(self):
        dkey, _ = econ_mod.match_district(
            "M-1 Light Industrial", {"MU-11": {}, "M-1": {}, "DEFAULT": {}})
        self.assertEqual(dkey, "M-1")

    def test_unmatched_label_falls_back_to_default(self):
        dkey, fallback = econ_mod.match_district(
            "R-1-8 (synthetic demo)", {"MU-11": {}, "DEFAULT": {}})
        self.assertEqual(dkey, "DEFAULT")
        self.assertTrue(fallback)

    def test_longest_token_wins(self):
        dkey, _ = econ_mod.match_district(
            "MU-11", {"MU-1": {}, "MU-11": {}, "DEFAULT": {}})
        self.assertEqual(dkey, "MU-11")


class TestEconomicsMapping(unittest.TestCase):
    def test_known_district_maps_expected_values(self):
        econ = load_econ()
        cfg = econ_mod.finance_config_from_economics(econ, "MU-11 (SLC)")
        self.assertEqual(cfg["sale_price_per_lot"],
                         econ["districts"]["MU-11"]["finished_lot_revenue"]["value"])
        self.assertEqual(cfg["road_cost_per_lf"],
                         econ["road_cost_per_lf"]["value"])
        self.assertEqual(cfg["soft_costs_fixed"],
                         econ["soft_costs"]["fixed_planning_value"]["value"])
        self.assertEqual(cfg["contingency_pct"],
                         econ["contingency_pct"]["value"])
        self.assertFalse(cfg["economics"]["fallback_to_default"])
        self.assertEqual(cfg["economics"]["district_matched"], "MU-11")

    def test_unmatched_zone_uses_default_and_flags_fallback(self):
        econ = load_econ()
        cfg = econ_mod.finance_config_from_economics(
            econ, "R-1-8 (synthetic demo)")
        self.assertEqual(cfg["sale_price_per_lot"],
                         econ["districts"]["DEFAULT"]["finished_lot_revenue"]["value"])
        self.assertTrue(cfg["economics"]["fallback_to_default"])
        self.assertEqual(cfg["economics"]["district_matched"], "DEFAULT")

    def test_os_pl_map_to_zero_revenue_with_warning(self):
        econ = load_econ()
        for label in ("OS Open Space", "PL Public Lands"):
            cfg = econ_mod.finance_config_from_economics(econ, label)
            self.assertEqual(cfg["sale_price_per_lot"], 0.0)
            self.assertTrue(cfg["economics"]["warnings"],
                            msg=f"no warning for {label}")

    def test_provenance_carries_confidence_and_source(self):
        econ = load_econ()
        cfg = econ_mod.finance_config_from_economics(econ, "M-1")
        prov = cfg["economics"]
        # M-1 revenue is the Caddy listing-sample figure (agent_agreed, not
        # human-verified); its confidence must flow through honestly.
        self.assertEqual(prov["revenue_confidence"], "sourced-from-listings")
        self.assertIn("source", cfg)
        self.assertIn("M-1", cfg["source"])

    def test_negative_mapped_value_refuses(self):
        econ = load_econ()
        bad = copy.deepcopy(econ)
        bad["road_cost_per_lf"]["value"] = -5
        with self.assertRaises(ValueError):
            econ_mod.finance_config_from_economics(bad, "MU-11")


class TestEconomicsSchema(unittest.TestCase):
    def test_every_figure_carries_source_date_confidence(self):
        econ = load_econ()

        def walk(obj, where="$"):
            if isinstance(obj, dict):
                if "value" in obj:
                    for tag in ("source", "date", "confidence"):
                        self.assertIn(tag, obj,
                                      msg=f"figure at {where} missing '{tag}'")
                    self.assertIn(obj["confidence"], econ_mod.CONFIDENCES,
                                  msg=f"figure at {where} bad confidence")
                for k, v in obj.items():
                    if not k.startswith("_"):
                        walk(v, f"{where}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    walk(v, f"{where}[{i}]")
        walk(econ)

    def test_required_sections_present(self):
        econ = load_econ()
        for section in ("districts", "road_cost_per_lf", "soft_costs",
                        "contingency_pct"):
            self.assertIn(section, econ)
        self.assertIn("DEFAULT", econ["districts"])
        for dkey in ("MU-11", "MU-5", "MU-6", "M-1", "OS", "PL"):
            self.assertIn(dkey, econ["districts"],
                          msg=f"district {dkey} missing")

    def test_validate_rejects_untagged_figure(self):
        econ = load_econ()
        bad = copy.deepcopy(econ)
        del bad["road_cost_per_lf"]["source"]
        with self.assertRaises(ValueError):
            econ_mod.validate_economics(bad)

    def test_validate_rejects_missing_section(self):
        econ = load_econ()
        bad = copy.deepcopy(econ)
        del bad["contingency_pct"]
        with self.assertRaises(ValueError):
            econ_mod.validate_economics(bad)

    def test_validate_rejects_missing_default(self):
        econ = load_econ()
        bad = copy.deepcopy(econ)
        del bad["districts"]["DEFAULT"]
        with self.assertRaises(ValueError):
            econ_mod.validate_economics(bad)


class TestCliDefaultUnchanged(unittest.TestCase):
    def test_economics_flag_defaults_to_none(self):
        args = build_parser().parse_args([])
        self.assertIsNone(args.economics)
        # ... and the legacy finance default is untouched
        self.assertEqual(args.finance, "inputs/finance.json")


if __name__ == "__main__":
    unittest.main()
