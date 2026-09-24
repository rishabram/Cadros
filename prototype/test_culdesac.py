"""DW-GEOM1 focused tests: cul-de-sac strategy correctness and the Tripp Lane fix.

Covers the accuracy-taxonomy GEOMETRY fix for Tripp Lane Subdivision
(approved 12 lots; baseline generated 9). Success criterion from
benchmark/accuracy_taxonomy.md: the generated envelope contains a
10-14 lot scheme, with parent and all inputs unchanged.
"""
import json
import os
import unittest

from shapely.geometry import Polygon, shape

from . import geometry

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRIPP_PARENT = os.path.join(REPO, "benchmark", "samples", "tripp_lane_parent.geojson")
TRIPP_ZONING = {"min_lot_area_sqft": 6000, "min_frontage_ft": 60, "road_width_ft": 49}


def _load_tripp():
    with open(TRIPP_PARENT) as fh:
        g = json.load(fh)
    poly = shape(g["geometry"])
    return poly, [list(c) for c in poly.exterior.coords]


class TestCuldesacStrategy(unittest.TestCase):
    def test_deterministic(self):
        poly, coords = _load_tripp()
        s1, _ = geometry.plan_generation(coords, TRIPP_ZONING, "tripp", max_schemes=12)
        s2, _ = geometry.plan_generation(coords, TRIPP_ZONING, "tripp", max_schemes=12)
        self.assertEqual([s.fingerprint for s in s1], [s.fingerprint for s in s2])
        self.assertEqual([len(s.lots) for s in s1], [len(s.lots) for s in s2])

    def test_bulb_radius_is_citable_default(self):
        self.assertEqual(geometry.CULDESAC_BULB_RADIUS_FT, 50.0)

    def test_culdesac_params_carry_strategy_and_honest_inputs(self):
        poly, coords = _load_tripp()
        schemes, _ = geometry.plan_generation(coords, TRIPP_ZONING, "tripp", max_schemes=12)
        cul = [s for s in schemes if s.params.get("strategy") == "culdesac"]
        self.assertTrue(cul, "expected at least one cul-de-sac scheme")
        for s in cul:
            self.assertEqual(s.params["bulb_radius_ft"], 50.0)
            self.assertEqual(s.params["road_width_ft"], 49.0)  # input, unchanged

    def test_lots_valid_contained_and_nonoverlapping(self):
        poly, coords = _load_tripp()
        schemes, _ = geometry.plan_generation(coords, TRIPP_ZONING, "tripp", max_schemes=12)
        for s in schemes:
            lps = [Polygon(l.polygon) for l in s.lots]
            for lp, lot in zip(lps, s.lots):
                self.assertTrue(lp.is_valid, f"{s.scheme_id}/{lot.lot_id} invalid")
                # Contained in parent to numerical tolerance (covers() is an
                # exact predicate that fails on coincident-boundary FP noise;
                # the generator clips lots to the parent).
                outside = lp.difference(poly).area
                self.assertLess(
                    outside, 1.0,
                    f"{s.scheme_id}/{lot.lot_id} outside parent: {outside:.2f} sqft",
                )
                self.assertGreaterEqual(lot.area_sqft, 6000 * 0.98)
                self.assertGreaterEqual(lot.frontage_ft, 60 * 0.98)
            for i in range(len(lps)):
                for j in range(i + 1, len(lps)):
                    self.assertLessEqual(
                        lps[i].intersection(lps[j]).area, 1.0,
                        f"{s.scheme_id} lots {i},{j} overlap",
                    )

    def test_bulb_lots_front_on_bulb_arc(self):
        """Wedge lots must actually touch the bulb circle (not be stranded).

        The wedge angular width is dtheta = module / bulb_r, so a bulb lot's
        designed frontage is the bulb arc ~= module. At least one lot in the
        top cul-de-sac scheme must exhibit that signature.
        """
        poly, coords = _load_tripp()
        schemes, _ = geometry.plan_generation(coords, TRIPP_ZONING, "tripp", max_schemes=12)
        top_cul = max(
            (s for s in schemes if s.params.get("strategy") == "culdesac"),
            key=lambda s: len(s.lots),
        )
        module = top_cul.params["lot_module_ft"]
        arc_frontages = [
            l.frontage_ft for l in top_cul.lots
            if abs(l.frontage_ft - module) / module < 0.05
        ]
        self.assertTrue(
            arc_frontages,
            f"no bulb-arc lot found (module={module}); frontages="
            f"{sorted(l.frontage_ft for l in top_cul.lots)}",
        )

    def test_tripp_envelope_reaches_10_to_14(self):
        """The DW-GEOM1 success criterion: envelope contains a 10-14 lot
        scheme with parent and all inputs unchanged."""
        poly, coords = _load_tripp()
        schemes, _ = geometry.plan_generation(coords, TRIPP_ZONING, "tripp", max_schemes=12)
        counts = sorted(len(s.lots) for s in schemes)
        self.assertTrue(
            any(10 <= c <= 14 for c in counts),
            f"envelope {counts} does not contain a 10-14 lot scheme",
        )

    def test_spine_road_grid_unchanged(self):
        """The historic 24 spine-road configs are untouched by the fix."""
        spine = [p for p in geometry.candidate_params(TRIPP_ZONING)
                 if p.get("strategy") == "spine_road"]
        self.assertEqual(len(spine), 24)
        self.assertEqual(
            sorted({p["angle_deg"] for p in spine}), [0.0, 30.0, 60.0, 90.0]
        )


if __name__ == "__main__":
    unittest.main()
