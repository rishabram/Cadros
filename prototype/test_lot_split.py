"""Tests for the lot-split scheme family (DW-GEOM2)."""
import json
import unittest

from shapely.geometry import shape

from . import geometry


def _fields_parent():
    g = json.load(open('benchmark/samples/taylorsville_fields_parent.geojson'))
    poly = shape(g['geometry'])
    return [list(c) for c in poly.exterior.coords]


FIELDS_ZONING = {
    'min_lot_area_sqft': 10000,
    'min_frontage_ft': 80,
    'road_width_ft': 0,
}


class LotSplitTest(unittest.TestCase):
    def test_fields_parent_yields_schemes(self):
        """Fields Subdivision (2-lot approved) must yield lot-split schemes."""
        coords = _fields_parent()
        schemes = geometry.plan_generation_split(
            coords, FIELDS_ZONING, 'fields', max_schemes=4)
        self.assertGreater(len(schemes), 0,
            "Lot-split family yielded 0 schemes for Fields parent")
        # At least one 2-lot scheme (matching the approved count).
        two_lot = [s for s in schemes if len(s.lots) == 2]
        self.assertGreater(len(two_lot), 0,
            "No 2-lot scheme found (approved=2)")

    def test_all_lots_meet_min_area(self):
        coords = _fields_parent()
        schemes = geometry.plan_generation_split(
            coords, FIELDS_ZONING, 'fields', max_schemes=8)
        for s in schemes:
            for lot in s.lots:
                self.assertGreaterEqual(
                    lot.area_sqft, 10000 * 0.999,
                    f"Lot {lot.lot_id} area {lot.area_sqft} < 10000")

    def test_no_roads_in_split_schemes(self):
        """Lot-splits have no new streets."""
        coords = _fields_parent()
        schemes = geometry.plan_generation_split(
            coords, FIELDS_ZONING, 'fields', max_schemes=4)
        for s in schemes:
            self.assertEqual(s.roads, [],
                f"Split scheme {s.scheme_id} has roads (should be none)")

    def test_lots_cover_parent(self):
        """Split lots should partition the parent (no gaps/overlaps)."""
        from shapely.ops import unary_union
        from shapely.geometry import Polygon
        coords = _fields_parent()
        parent = geometry.to_polygon(coords)
        schemes = geometry.plan_generation_split(
            coords, FIELDS_ZONING, 'fields', max_schemes=4)
        for s in schemes:
            polys = [Polygon(lot.polygon) for lot in s.lots]
            union = unary_union(polys)
            # Union area should match parent (within 1%).
            self.assertAlmostEqual(
                union.area, parent.area, delta=parent.area * 0.01,
                msg=f"Scheme {s.scheme_id}: union {union.area:.0f} vs "
                    f"parent {parent.area:.0f}")

    def test_deterministic(self):
        coords = _fields_parent()
        s1 = geometry.plan_generation_split(coords, FIELDS_ZONING, 'f', max_schemes=4)
        s2 = geometry.plan_generation_split(coords, FIELDS_ZONING, 'f', max_schemes=4)
        self.assertEqual([s.scheme_id for s in s1],
                         [s.scheme_id for s in s2])
        self.assertEqual([s.fingerprint for s in s1],
                         [s.fingerprint for s in s2])

    def test_plan_generation_falls_back_to_split(self):
        """plan_generation uses lot-split when street strategies yield 0."""
        coords = _fields_parent()
        schemes, diag = geometry.plan_generation(
            coords, FIELDS_ZONING, 'fields', max_schemes=8)
        self.assertGreater(len(schemes), 0,
            "plan_generation yielded 0 schemes (lot-split fallback failed)")
        self.assertTrue(diag.get("lot_split_used", False),
            "lot_split_used not set in diagnostic")


if __name__ == '__main__':
    unittest.main()
