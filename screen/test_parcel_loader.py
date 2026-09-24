"""Unit tests for parcel_loader.py (W2). All test geometries are SYNTHETIC.

Run from the neron-scratch root:
    venv/bin/python -m unittest screen.test_parcel_loader
"""
import json
import os
import tempfile
import unittest

from screen.parcel_loader import (
    _esri_rings_to_polygons,
    _wkid_to_epsg,
    join_zoning,
    load_parcels,
    LOCAL_FEET_EPSG,
)

SYNTH_ESRI = {
    "spatialReference": {"wkid": 4326, "latestWkid": 4326},
    "features": [
        {
            "attributes": {"OBJECTID": 1, "PARCEL_ID": "TEST-001",
                           "PARCEL_ADD": "1 Test St", "PARCEL_CITY": "Testville",
                           "County": "SaltLake"},
            "geometry": {"rings": [[
                [-111.90, 40.76], [-111.899, 40.76],
                [-111.899, 40.761], [-111.90, 40.761], [-111.90, 40.76]]]}},
        {
            "attributes": {"OBJECTID": 2},  # no PARCEL_ID -> falls back to OBJECTID
            "geometry": {"rings": [[
                [-111.89, 40.75], [-111.888, 40.75],
                [-111.888, 40.752], [-111.89, 40.752], [-111.89, 40.75]]]}},
        {"attributes": {"OBJECTID": 3, "PARCEL_ID": "BAD"}, "geometry": None},  # dropped
    ],
}

SYNTH_ZONING = {
    "spatialReference": {"wkid": 4326},
    "features": [{
        "attributes": {"OBJECTID": 1, "ZONING": "MU-11", "ZONING_NAME": "Mixed Use"},
        "geometry": {"rings": [[
            [-111.91, 40.755], [-111.898, 40.755],
            [-111.898, 40.762], [-111.91, 40.762], [-111.91, 40.755]]]}},
    ],
}


def _tmp_json(doc):
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(doc, fh)
    return path


class TestParcelLoader(unittest.TestCase):
    def test_wkid_mapping(self):
        self.assertEqual(_wkid_to_epsg(102100), 3857)
        self.assertEqual(_wkid_to_epsg(102743), 3566)
        self.assertEqual(_wkid_to_epsg(4326), 4326)

    def test_esri_rings_with_hole(self):
        outer = [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
        hole = [[3, 3], [3, 7], [7, 7], [7, 3], [3, 3]]
        polys = _esri_rings_to_polygons([outer, hole])
        self.assertEqual(len(polys), 1)
        self.assertAlmostEqual(polys[0].area, 84.0, places=6)

    def test_load_parcels_drops_holes(self):
        doc = {
            "spatialReference": {"wkid": 4326},
            "features": [{
                "attributes": {"PARCEL_ID": "HOLE"},
                "geometry": {"rings": [
                    [[-111.90, 40.76], [-111.899, 40.76], [-111.899, 40.761],
                     [-111.90, 40.761], [-111.90, 40.76]],
                    [[-111.8997, 40.7602], [-111.8993, 40.7602], [-111.8993, 40.7606],
                     [-111.8997, 40.7606], [-111.8997, 40.7602]]]},
            }],
        }
        feats = load_parcels(_tmp_json(doc))
        self.assertEqual(len(feats), 1)
        self.assertEqual(len(feats[0]["geometry"]["coordinates"]), 1)  # exterior only

    def test_load_parcels_schema_and_feet(self):
        path = _tmp_json(SYNTH_ESRI)
        feats = load_parcels(path)
        self.assertEqual(len(feats), 2)  # BAD geometry dropped
        f0 = feats[0]
        self.assertEqual(f0["geometry"]["type"], "Polygon")
        self.assertEqual(f0["properties"]["parcel_id"], "TEST-001")
        self.assertEqual(f0["properties"]["crs"], "local-feet")
        self.assertEqual(f0["properties"]["address"], "1 Test St")
        # Coordinates must be in Utah state-plane feet magnitude, not degrees.
        x0 = f0["geometry"]["coordinates"][0][0][0]
        self.assertTrue(1_300_000 < x0 < 1_800_000, x0)
        self.assertEqual(feats[1]["properties"]["parcel_id"], "2")  # OBJECTID fallback

    def test_load_parcels_limit_and_bbox(self):
        path = _tmp_json(SYNTH_ESRI)
        self.assertEqual(len(load_parcels(path, limit=1)), 1)
        # bbox far away in feet frame -> nothing
        self.assertEqual(load_parcels(path, bbox=(0, 0, 100, 100)), [])

    def test_join_zoning_attaches_district(self):
        ppath = _tmp_json(SYNTH_ESRI)
        zpath = _tmp_json(SYNTH_ZONING)
        feats = join_zoning(load_parcels(ppath), zpath)
        self.assertEqual(feats[0]["properties"]["district"], "MU-11")
        self.assertEqual(feats[0]["properties"]["zone_label"], "Mixed Use")
        self.assertIn(feats[0]["properties"]["district_provenance"],
                      ("centroid-contains", "nearest"))
        # Second parcel is outside the zone polygon -> nearest fallback still attaches
        self.assertIn("district", feats[1]["properties"])

    def test_join_zoning_does_not_override_explicit_district(self):
        ppath = _tmp_json(SYNTH_ESRI)
        zpath = _tmp_json(SYNTH_ZONING)
        feats = load_parcels(ppath)
        feats[0]["properties"]["district"] = "M-1"
        feats = join_zoning(feats, zpath)
        self.assertEqual(feats[0]["properties"]["district"], "M-1")


if __name__ == "__main__":
    unittest.main()
