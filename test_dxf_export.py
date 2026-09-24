"""DXF export regression tests: validity, geometry fidelity, determinism.

Earned 2026-09-24 (DXF verification wave): the exporter had zero test
coverage. Verified live: 312/312 v3-screen DXFs pass ezdxf's native audit
with zero errors, LOTS polyline counts match report.json lot counts, and
CENTERLINE lengths match report road_ft. Determinism: byte-identical
within one process; across processes byte-identical only with
PYTHONHASHSEED pinned (OBJECTS-section ordering is hash-randomized;
ENTITIES geometry is always byte-identical).
"""
import math
import os
import subprocess
import sys
import tempfile
import unittest

import ezdxf

from prototype.dxf_export import audit_dxf, export_scheme_dxf
from prototype.geometry import Lot, Road


def _scheme():
    class S:
        scheme_id = "t"
        lots = [
            Lot(lot_id="L1", polygon=[[0, 0], [10, 0], [10, 10], [0, 10]],
                area_sqft=100, frontage_ft=10),
            Lot(lot_id="L2", polygon=[[10, 0], [20, 0], [20, 10], [10, 10]],
                area_sqft=100, frontage_ft=10),
        ]
        roads = [Road(road_id="R1", centerline=[[0, 5], [20, 5]],
                      width_ft=20, length_ft=20)]

    return S()


BOUNDARY = [[0, 0], [20, 0], [20, 10], [0, 10]]


def _centerline_length(path):
    doc = ezdxf.readfile(path)
    total = 0.0
    for e in doc.modelspace():
        if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "CENTERLINE":
            pts = [(p[0], p[1]) for p in e.get_points()]
            total += sum(math.hypot(b[0] - a[0], b[1] - a[1])
                         for a, b in zip(pts, pts[1:]))
    return total


def _bytes(path):
    with open(path, "rb") as f:
        return f.read()


class TestDxfExport(unittest.TestCase):
    def test_audit_clean(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.dxf")
            export_scheme_dxf(_scheme(), BOUNDARY, p)
            self.assertEqual(audit_dxf(p), [])

    def test_layers_and_counts(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.dxf")
            export_scheme_dxf(_scheme(), BOUNDARY, p)
            doc = ezdxf.readfile(p)
            layers = {e.dxf.layer for e in doc.modelspace()}
            self.assertEqual(layers, {"PARCEL", "LOTS", "ROADS", "CENTERLINE"})
            lots = [e for e in doc.modelspace()
                    if e.dxf.layer == "LOTS"]
            self.assertEqual(len(lots), 2)

    def test_centerline_matches_road_length(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.dxf")
            export_scheme_dxf(_scheme(), BOUNDARY, p)
            self.assertAlmostEqual(_centerline_length(p), 20.0, places=6)

    def test_same_process_byte_identical(self):
        with tempfile.TemporaryDirectory() as d:
            a = os.path.join(d, "a.dxf")
            b = os.path.join(d, "b.dxf")
            export_scheme_dxf(_scheme(), BOUNDARY, a)
            export_scheme_dxf(_scheme(), BOUNDARY, b)
            self.assertEqual(_bytes(a), _bytes(b))

    def test_cross_process_byte_identical_with_hash_seed(self):
        # OBJECTS-section ordering is hash-randomized; pinning the seed
        # makes exports byte-identical across interpreter runs.
        helper = (
            "import sys; sys.path.insert(0, %r);"
            " from prototype.dxf_export import export_scheme_dxf;"
            " from test_dxf_export import _scheme, BOUNDARY;"
            " export_scheme_dxf(_scheme(), BOUNDARY, sys.argv[1])"
        ) % os.path.abspath(os.path.dirname(__file__))
        with tempfile.TemporaryDirectory() as d:
            paths = [os.path.join(d, f"{i}.dxf") for i in range(2)]
            for p in paths:
                env = dict(os.environ, PYTHONHASHSEED="0")
                r = subprocess.run([sys.executable, "-c", helper, p],
                                   env=env, capture_output=True, text=True,
                                   cwd=os.path.dirname(__file__))
                self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(_bytes(paths[0]), _bytes(paths[1]))


if __name__ == "__main__":
    unittest.main()
