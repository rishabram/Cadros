"""Fast DXF writer — direct text generation (DW-DXF1).

The ezdxf object model spends ~69ms per scheme serializing LWPOLYLINE
entities (tag-by-tag). For bulk export (10k-parcel stress runs), this is
~52% of per-parcel time.

This module writes minimal valid DXF directly as text: HEADER + TABLES
(layers) + ENTITIES (LWPOLYLINEs) + EOF. No object model, no per-tag
overhead — just string building. ~1ms per scheme (50-70x faster).

Byte-equivalence contract: the fast writer produces CAD content identical
to the ezdxf path (same layers, same entities, same vertex coordinates).
Proven by round-trip: both files parsed with ezdxf, entities compared.
See prototype/test_dxf_performance.py.

The ezdxf path (dxf_export.export_scheme_dxf) remains the reference for
byte-identical provenance; the fast path is for bulk export where the
content (not the exact bytes) is what matters.
"""
from __future__ import annotations

from typing import List

from shapely.geometry import LineString


def _closed(coords: List[List[float]]) -> List[List[float]]:
    if coords and (coords[0] != coords[-1]):
        return coords + [coords[0]]
    return coords


def _lwpolyline_dxf(layer: str, coords: List[List[float]], closed: bool, handle: int) -> List[str]:
    """DXF tags for one LWPOLYLINE entity (group codes 3-char padded)."""
    n = len(coords)
    flag = 1 if closed else 0
    lines = [
        "0", "LWPOLYLINE",
        "  5", f"{handle:X}",
        "100", "AcDbEntity",
        "  8", layer,
        "100", "AcDbPolyline",
        " 90", str(n),
        " 70", str(flag),
    ]
    for x, y in coords:
        lines.extend([" 10", f"{x:.2f}", " 20", f"{y:.2f}"])
    return lines


def export_scheme_dxf_fast(scheme, parcel_coords: List[List[float]], path: str) -> None:
    """Write a minimal valid DXF directly (fast path)."""
    out: List[str] = []
    # HEADER
    out.extend([
        "0", "SECTION", "  2", "HEADER",
        "  9", "$INSUNITS", " 70", "2",  # feet
        "0", "ENDSEC",
    ])
    # TABLES (layers)
    out.extend(["0", "SECTION", "  2", "TABLES", "0", "TABLE", "  2", "LAYER", " 70", "4"])
    handle = 0x10
    for name, color in (("PARCEL", 5), ("LOTS", 3), ("ROADS", 1), ("CENTERLINE", 2)):
        out.extend([
            "0", "LAYER", "  5", f"{handle:X}",
            "100", "AcDbSymbolTableRecord", "100", "AcDbLayerTableRecord",
            "  2", name, " 70", "0", " 62", str(color), "  6", "Continuous",
        ])
        handle += 1
    out.extend(["0", "ENDTAB", "0", "ENDSEC"])
    # BLOCKS (minimal — required for valid DXF structure)
    out.extend([
        "0", "SECTION", "  2", "BLOCKS",
        "0", "BLOCK", "  5", f"{handle:X}", "100", "AcDbEntity",
        "  8", "0", "100", "AcDbBlockBegin", "  2", "*Model_Space",
        " 70", "0", " 10", "0.0", " 20", "0.0", " 30", "0.0",
        "0", "ENDBLK", "  5", f"{handle+1:X}", "100", "AcDbEntity",
        "  8", "0", "100", "AcDbBlockEnd",
        "0", "ENDSEC",
    ])
    handle += 2
    # ENTITIES
    out.extend(["0", "SECTION", "  2", "ENTITIES"])
    out.extend(_lwpolyline_dxf("PARCEL", _closed(parcel_coords), True, handle)); handle += 1
    for lot in scheme.lots:
        out.extend(_lwpolyline_dxf("LOTS", _closed(lot.polygon), True, handle)); handle += 1
    for road in scheme.roads:
        band = LineString(road.centerline).buffer(road.width_ft / 2, cap_style=2)
        exterior = [[round(x, 2), round(y, 2)] for x, y in band.exterior.coords]
        out.extend(_lwpolyline_dxf("ROADS", exterior, True, handle)); handle += 1
        out.extend(_lwpolyline_dxf("CENTERLINE", road.centerline, False, handle)); handle += 1
    out.extend(["0", "ENDSEC", "0", "EOF"])
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")
