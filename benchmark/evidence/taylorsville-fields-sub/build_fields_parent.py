#!/usr/bin/env python3
"""GreenRush-14: build the Fields Subdivision historical parent polygon.

Reconstructs the pre-development parent (21111020270000, retired) as the
deterministic shapely union of its two recorded children (both still current
in UGRC Parcels_SaltLake, ParcelYear 2026), then reprojects to
pipeline-native local feet (azimuthal equidistant about centroid, meters ->
US survey feet, translated to bbox-minimum origin) — the same convention as
benchmark/samples/daybreak_v12b_plat1_parent.geojson.

Deterministic: script, not model geometry. No wall-clock timestamps in output.
"""
import json
import math
import os

from shapely.geometry import shape
from shapely.ops import unary_union

BASE = os.path.dirname(os.path.abspath(__file__))
CHILDREN = os.path.join(BASE, "children.geojson")
OUT = os.path.join(BASE, "..", "..", "samples", "taylorsville_fields_parent.geojson")

FT_PER_M = 3.280833333  # US survey foot


def to_local_feet(geom, lon0, lat0):
    """Azimuthal-equidistant projection about (lon0, lat0); meters->ft."""
    lat0r = math.radians(lat0)
    cos_lat0 = math.cos(lat0r)

    def proj(lon, lat):
        x = math.radians(lon - lon0) * cos_lat0 * 6378137.0
        y = math.radians(lat - lat0) * 6378137.0
        return (x * FT_PER_M, y * FT_PER_M)

    def xf_ring(ring):
        return [proj(lon, lat) for lon, lat in ring]

    if geom.geom_type == "Polygon":
        return {
            "type": "Polygon",
            "coordinates": [xf_ring(geom.exterior.coords)]
            + [xf_ring(r.coords) for r in geom.interiors],
        }
    if geom.geom_type == "MultiPolygon":
        polys = []
        for p in geom.geoms:
            polys.append(
                [xf_ring(p.exterior.coords)]
                + [xf_ring(r.coords) for r in p.interiors]
            )
        return {"type": "MultiPolygon", "coordinates": polys}
    raise ValueError(f"unexpected geometry type {geom.geom_type}")


def main():
    with open(CHILDREN) as f:
        fc = json.load(f)
    polys = [shape(f["geometry"]) for f in fc["features"]]
    assert len(polys) == 2, "expected exactly 2 child parcels"
    union = unary_union(polys)
    print("union type:", union.geom_type, "valid:", union.is_valid)
    assert union.is_valid, "union is not a valid polygon"

    # Area check in a metric frame before final reprojection
    lon0, lat0 = union.centroid.x, union.centroid.y
    gj = to_local_feet(union, lon0, lat0)

    # Translate to bbox-minimum origin (pipeline-native local feet convention)
    rings = (
        [gj["coordinates"]] if gj["type"] == "Polygon" else gj["coordinates"]
    )
    xs = [x for poly in rings for ring in poly for x, _ in ring]
    ys = [y for poly in rings for ring in poly for _, y in ring]
    minx, miny = min(xs), min(ys)
    if gj["type"] == "Polygon":
        gj["coordinates"] = [
            [[x - minx, y - miny] for x, y in ring]
            for ring in gj["coordinates"]
        ]
    else:
        gj["coordinates"] = [
            [[[x - minx, y - miny] for x, y in ring] for ring in poly]
            for poly in gj["coordinates"]
        ]

    # Pipeline reads geometry.coordinates[0] as the outer ring of a single
    # polygon; MultiPolygon input must not pass through silently.
    if gj["type"] != "Polygon":
        raise ValueError(
            f"union is {gj['type']}, not a single Polygon — harness requires "
            "one outer ring; refusing to silently drop pieces"
        )

    area_sqft = shape(
        {"type": "Polygon", "coordinates": gj["coordinates"]}
    ).area
    area_ac = area_sqft / 43560.0
    print(f"union area: {area_sqft:,.1f} sqft = {area_ac:.4f} ac "
          f"(official 0.72 ac)")

    feature = {
        "type": "Feature",
        "properties": {
            "crs": "local-feet",
            "name": "FIELDS SUBDIVISION - reconstructed parent "
                    "(4768 S 1175 W)",
            "plat_id": "taylorsville-fields-sub",
            "parcel_id": "21111020270000",
            "parent_parcel_desc": "21111020270000 (retired pre-subdivision "
                                  "parcel; not in current UGRC). "
                                  "Reconstructed as deterministic shapely "
                                  "union of the two recorded children.",
            "child_parcel_ids": ["21111020370000", "21111020380000"],
            "child_count": 2,
            "union_area_sqft": round(area_sqft, 1),
            "union_area_ac": round(area_ac, 4),
            "projection": "azimuthal equidistant about centroid "
                          f"({lon0:.6f}, {lat0:.6f}); US survey feet; "
                          "bbox-minimum origin",
            "built_by": "GreenRush-14 build_fields_parent.py (script, not "
                        "model geometry), 2026-09-24",
        },
        "geometry": gj,
    }
    with open(OUT, "w") as f:
        json.dump(feature, f)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
