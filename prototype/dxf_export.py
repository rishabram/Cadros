"""CAD export — scheme -> DXF via ezdxf (CAD compiler §1, scaffold v0).

Layers: PARCEL (boundary), LOTS (closed lot polylines), ROADS (road band),
CENTERLINE (road centerline). Units: feet ($INSUNITS=2).
"""
from __future__ import annotations

from typing import List

import ezdxf
from shapely.geometry import LineString

# Deterministic CAD export: ezdxf stamps per-run random GUIDs, creation
# timestamps, and "version @ timestamp" markers into every file. This
# first-class option pins all of them so identical inputs produce
# byte-identical DXF artifacts (provenance / regression checks).
#
# Precision note (verified 2026-09-24): within one interpreter process the
# export is byte-deterministic. Across processes, ezdxf's OBJECTS section
# (paper-space LAYOUT bookkeeping — no geometry) serializes in an order that
# depends on Python's hash randomization, so file bytes can differ while the
# ENTITIES section (all CAD geometry) stays byte-identical. For
# byte-identical files across processes, run with PYTHONHASHSEED=0.
ezdxf.options.write_fixed_meta_data_for_testing = True


def _closed(coords: List[List[float]]) -> List[List[float]]:
    if coords and (coords[0] != coords[-1]):
        return coords + [coords[0]]
    return coords


def export_scheme_dxf(scheme, parcel_coords: List[List[float]], path: str) -> None:
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 2  # feet
    msp = doc.modelspace()
    for name, color in (("PARCEL", 5), ("LOTS", 3), ("ROADS", 1), ("CENTERLINE", 2)):
        if name not in doc.layers:
            doc.layers.add(name, color=color)

    msp.add_lwpolyline(_closed(parcel_coords), close=True, dxfattribs={"layer": "PARCEL"})
    for lot in scheme.lots:
        msp.add_lwpolyline(_closed(lot.polygon), close=True, dxfattribs={"layer": "LOTS"})
    for road in scheme.roads:
        band = LineString(road.centerline).buffer(road.width_ft / 2, cap_style=2)
        exterior = list(band.exterior.coords)
        msp.add_lwpolyline(
            [[round(x, 2), round(y, 2)] for x, y in exterior],
            close=True,
            dxfattribs={"layer": "ROADS"},
        )
        msp.add_lwpolyline(
            road.centerline, close=False, dxfattribs={"layer": "CENTERLINE"}
        )
    doc.saveas(path)


def audit_dxf(path: str) -> List[str]:
    """Reopen + audit a DXF (native CAD validity metric, build plan §14)."""
    doc = ezdxf.readfile(path)
    auditor = doc.audit()
    return [e.message for e in auditor.errors]
