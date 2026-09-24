"""Bearing/distance traverse -> polygon. Deterministic; no model interpretation.

Used to reconstruct an approved plat's parent-parcel boundary from the
metes-and-bounds description printed on the recorded plat.
Verified 2026-09-24 on THE MILL SUBDIVISION PLAT (South Salt Lake):
  closure error 0.003 ft on ~2500 ft perimeter;
  computed area 231,614.4 sqft vs plat-stated 231,617 (delta 2.6 sqft, rounding).
"""
from __future__ import annotations

import json
import math


def bearing_to_azimuth_rad(ns: str, d: float, m: float, s: float, ew: str) -> float:
    dec = d + m / 60.0 + s / 3600.0
    table = {"NE": dec, "SE": 180 - dec, "SW": 180 + dec, "NW": 360 - dec}
    return math.radians(table[ns + ew])


def traverse(legs, start=(0.0, 0.0)):
    """legs: iterable of (ns, deg, min, sec, ew, distance_ft). Returns closed point list."""
    pts = [tuple(start)]
    for ns, d, m, s, ew, dist in legs:
        az = bearing_to_azimuth_rad(ns, d, m, s, ew)
        x, y = pts[-1]
        pts.append((x + dist * math.sin(az), y + dist * math.cos(az)))
    return pts


def polygon_area_sqft(pts) -> float:
    return abs(sum(pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1]
                   for i in range(len(pts) - 1))) / 2.0


def to_geojson_feature(pts, parcel_id: str, note: str) -> dict:
    ring = [[round(x, 3), round(y, 3)] for x, y in pts]
    ring[-1] = ring[0]  # explicit closure (traverse closure error was 0.003 ft)
    return {
        "type": "Feature",
        "properties": {"parcel_id": parcel_id, "crs": "local-feet", "note": note},
        "geometry": {"type": "Polygon", "coordinates": [ring]},
    }


if __name__ == "__main__":
    # THE MILL SUBDIVISION PLAT boundary (from plat text; POB = local origin)
    mill_legs = [
        ("N", 89, 49, 46, "E", 721.37),
        ("S", 0, 3, 6, "W", 388.02),
        ("S", 89, 49, 46, "W", 371.57),
        ("N", 0, 0, 28, "E", 138.00),
        ("S", 89, 49, 46, "W", 349.50),
        ("N", 0, 0, 28, "E", 250.02),
    ]
    pts = traverse(mill_legs)
    print("closure error ft:", round(math.dist(pts[0], pts[-1]), 4))
    area = polygon_area_sqft(pts)
    print(f"area: {area:,.1f} sqft = {area / 43560:.3f} acres (plat: 231,617 / 5.317)")
    feat = to_geojson_feature(pts, "mill-subdivision-parent",
                              "THE MILL SUBDIVISION PLAT, South Salt Lake City, SLCo — "
                              "boundary reconstructed from recorded plat metes-and-bounds")
    with open("samples/mill_subdivision_parent.geojson", "w") as f:
        json.dump(feat, f)
    print("wrote samples/mill_subdivision_parent.geojson")
