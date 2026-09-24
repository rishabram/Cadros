"""Tests for the attached-twinhome product mode (DW-PROD1).

Width-less frontage semantics: R-N-B §17.140.040 states a 5,000 sqft minimum
lot area and setbacks but NO minimum lot width; ZONING_POLICY forbids
inventing a width proxy. The attached mode therefore runs WITHOUT
min_frontage_ft: lot modules are product unit widths (explicit design search,
not a zoning claim), the frontage filter is disabled, but frontage is still
measured and reported per lot.
"""
import json
import unittest

from . import geometry


def _rect_parcel(w=400.0, h=300.0):
    return [(0, 0), (w, 0), (w, h), (0, h)]


ATTACHED_ZONING = {
    "product_type": "attached_twinhome",
    "min_lot_area_sqft": 5000,
    # NOTE: no min_frontage_ft — width-less by design.
    "road_width_ft": 49,
}

DETACHED_ZONING = {
    "min_lot_area_sqft": 6000,
    "min_frontage_ft": 60,
    "road_width_ft": 49,
}


class AttachedProductTest(unittest.TestCase):
    def test_runs_without_min_frontage(self):
        """The pipeline must not raise when min_frontage_ft is absent."""
        schemes, _ = geometry.plan_generation(
            _rect_parcel(), ATTACHED_ZONING, "syn-attached", max_schemes=12)
        self.assertGreater(len(schemes), 0)

    def test_product_widths_in_grid(self):
        """Attached grid uses product unit widths (30/35/40), not frontage."""
        params = geometry.candidate_params(ATTACHED_ZONING)
        modules = sorted({p["lot_module_ft"] for p in params})
        self.assertEqual(modules, [30.0, 35.0, 40.0])

    def test_no_frontage_filter_but_frontage_reported(self):
        """Lots may have frontage below any threshold; area still gated."""
        schemes, _ = geometry.plan_generation(
            _rect_parcel(), ATTACHED_ZONING, "syn-attached", max_schemes=12)
        self.assertGreater(len(schemes), 0)
        for s in schemes:
            for lot in s.lots:
                # area gate holds (98% tolerance)
                self.assertGreaterEqual(lot.area_sqft, 5000 * 0.98)
                # frontage is measured and reported (may be narrow — width-less)
                self.assertGreater(lot.frontage_ft, 0)

    def test_deterministic(self):
        """Same inputs -> same fingerprints."""
        s1, _ = geometry.plan_generation(
            _rect_parcel(), ATTACHED_ZONING, "syn-attached", max_schemes=12)
        s2, _ = geometry.plan_generation(
            _rect_parcel(), ATTACHED_ZONING, "syn-attached", max_schemes=12)
        f1 = [s.fingerprint for s in s1]
        f2 = [s.fingerprint for s in s2]
        self.assertEqual(f1, f2)

    def test_detached_frontage_filter_intact(self):
        """Detached mode still requires and enforces min_frontage_ft."""
        params = geometry.candidate_params(DETACHED_ZONING)
        modules = sorted({p["lot_module_ft"] for p in params if p["strategy"] == "spine_road"})
        self.assertEqual(modules, [60.0, 75.0])
        # missing frontage on detached raises KeyError (fail loudly)
        bad = {"min_lot_area_sqft": 6000, "road_width_ft": 49}
        with self.assertRaises(KeyError):
            geometry.candidate_params(bad)

    def test_pipeline_accepts_widthless(self):
        """_validate_zoning allows missing frontage for attached only."""
        from .pipeline import _validate_zoning
        _validate_zoning(ATTACHED_ZONING)  # must not raise
        with self.assertRaises(ValueError):
            _validate_zoning({"min_lot_area_sqft": 6000, "road_width_ft": 49})


if __name__ == "__main__":
    unittest.main()
