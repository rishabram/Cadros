"""Tests for mixed-product scheme support (DW-MIX1).

Daybreak 11B Plat 2 (59 detached + 32 townhomes) cannot be represented in
the single-product harness. This module implements the representation
(product_specs, sub-parcel partition, per-product generation, lot
product_type tags) and proves it on synthetic inputs mirroring the plat's
mix + acreage (the plat's parent polygon and P-C dims are unsourced, so
synthetic stand-ins are labeled as such).
"""
import unittest

from . import geometry


# Synthetic P-C dims (LABELED SYNTHETIC — the plat's P-C dims are unsourced).
# Detached: 6,000 sqft / 60 ft frontage / 49 ft road.
# Townhome: 3,000 sqft / width-less (no frontage minimum) / 49 ft road.
DETACHED_ZONING = {
    "product_type": "detached",
    "min_lot_area_sqft": 6000,
    "min_frontage_ft": 60,
    "road_width_ft": 49,
}
TOWNHOME_ZONING = {
    "product_type": "attached_townhome",
    "min_lot_area_sqft": 3000,
    # no min_frontage_ft — width-less
    "road_width_ft": 49,
}

# 12.731 acres = 554,571 sqft. Synthetic rectangle 800 x 693 ft.
ACRE_12_731_SQFT = 12.731 * 43560
SYN_PARCEL = [(0, 0), (800, 0), (800, 693), (0, 693)]


def _mix_specs():
    return [
        {"product_type": "detached", "zoning": DETACHED_ZONING,
         "approved_units": 59},
        {"product_type": "attached_townhome", "zoning": TOWNHOME_ZONING,
         "approved_units": 32},
    ]


class MixedProductTest(unittest.TestCase):
    def test_partition_sums_to_parcel(self):
        """Sub-parcel areas sum to the parcel area (rectangle: exact)."""
        from shapely.geometry import Polygon
        poly = Polygon(SYN_PARCEL)
        subs = geometry._partition_parcel(poly, [0.65, 0.35])
        self.assertEqual(len(subs), 2)
        total = sum(s.area for s in subs)
        self.assertAlmostEqual(total, poly.area, delta=1.0)

    def test_mixed_generation_produces_tagged_lots(self):
        """Mixed schemes have lots tagged by product_type."""
        mixed, diag = geometry.plan_generation_mixed(
            SYN_PARCEL, _mix_specs(), "syn-v11b", max_schemes=5)
        self.assertGreater(len(mixed), 0)
        scheme = mixed[0]
        types = {lot.product_type for lot in scheme.lots}
        self.assertEqual(types, {"detached", "attached_townhome"})
        # Per-product counts reported.
        self.assertIn("per_product_counts", diag)
        counts = diag["per_product_counts"]
        self.assertGreater(counts["detached"], 0)
        self.assertGreater(counts["attached_townhome"], 0)

    def test_area_fractions_from_program(self):
        """Land allocated proportional to approved program (units x area)."""
        # Detached: 59*6000=354,000. Townhome: 32*3000=96,000. Total 450,000.
        # Detached fraction: 354/450=0.787. Townhome: 96/450=0.213.
        _, diag = geometry.plan_generation_mixed(
            SYN_PARCEL, _mix_specs(), "syn-v11b", max_schemes=3)
        fracs = diag["area_fractions"]
        self.assertAlmostEqual(fracs[0], 0.7867, places=3)
        self.assertAlmostEqual(fracs[1], 0.2133, places=3)

    def test_deterministic(self):
        """Same inputs -> same per-product counts and fingerprint."""
        m1, _ = geometry.plan_generation_mixed(
            SYN_PARCEL, _mix_specs(), "syn-v11b", max_schemes=5)
        m2, _ = geometry.plan_generation_mixed(
            SYN_PARCEL, _mix_specs(), "syn-v11b", max_schemes=5)
        self.assertEqual(m1[0].fingerprint, m2[0].fingerprint)

    def test_townhome_product_widths(self):
        """Townhome grid uses narrower product widths (22/26/30)."""
        params = geometry.candidate_params(TOWNHOME_ZONING)
        modules = sorted({p["lot_module_ft"] for p in params})
        self.assertEqual(modules, [22.0, 26.0, 30.0])

    def test_lot_schema_carries_product_type(self):
        """Lot.product_type defaults to detached; settable."""
        from .schema import Lot
        lot = Lot(lot_id="x", polygon=[[0, 0]], area_sqft=100, frontage_ft=10)
        self.assertEqual(lot.product_type, "detached")


if __name__ == "__main__":
    unittest.main()
