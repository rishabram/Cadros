#!/usr/bin/env python3
"""Parcel GIS loader for NERON mass screening (W2).

Reads real-world parcel GIS and emits W1-schema GeoJSON parcel Features:
  - geometry: Polygon in planar FEET
  - properties: parcel_id (str), crs ("local-feet"), optional district,
    optional zone_label

Primary source: Utah AGRC "Utah Statewide Parcels" ArcGIS REST Feature
Service (raw dumps saved as Esri FeatureSet JSON via f=json). Also accepts
plain GeoJSON FeatureCollections.

Real GIS arrives in lat/lon (EPSG:4326) or Web Mercator (102100). All
geometries are reprojected to a single canonical planar-feet frame:

    EPSG:3566 = NAD83 / Utah Central (ftUS)

That frame is the documented "local-feet" CRS for real parcels in Salt Lake
County. It is a fixed public CRS, NOT a per-parcel arbitrary origin: a given
parcel always maps to the same coordinates.

District attribution: parcels carry no zoning. Use join_zoning() to attach
the `district` / `zone_label` properties from the Salt Lake City open-data
"Zoning" layer (centroid-in-polygon; fallback to nearest zone centroid-wise
when no containing polygon is found, flagged in provenance).

Invariants:
  - Never invents parcels: every feature returned comes from the source file.
    No synthetic parcels are emitted (synthetic parcels live in the engine
    test corpus and are clearly labeled there).
  - MultiPolygon sources: only the LARGEST part is kept (schema requires
    Polygon); interior rings are dropped (W1 screener does not handle holes).
    Both transformations are documented, never silent.
  - Missing geometries or missing ids are dropped, never defaulted.

Usage:
    from parcel_loader import load_parcels, join_zoning

    feats = load_parcels("parcels_raw.json", limit=500)
    feats = join_zoning(feats, "zoning_raw.json")

CLI:
    python parcel_loader.py --source parcels_raw.json --zoning zoning_raw.json \\
        --sample 500 --out screen/real_parcels/
"""

import argparse
import json
import os
import sys

from shapely.geometry import Polygon, mapping
from shapely.ops import transform as shp_transform
from shapely.strtree import STRtree

# Canonical planar-feet frame for real parcels: NAD83 / Utah Central (ftUS).
LOCAL_FEET_EPSG = 3566

try:
    from pyproj import CRS, Transformer
except ImportError:  # pragma: no cover
    CRS = Transformer = None


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _esri_rings_to_polygons(rings):
    """Convert Esri 'rings' array to a list of shapely Polygons.

    Esri rings encode holes by clockwise orientation (in a right-hand-rule
    service). Rather than trust orientation, we use containment: a ring
    inside another polygon's exterior is treated as a hole.
    """
    polys = []
    outers = []
    for ring in rings:
        if len(ring) < 4:
            continue
        p = Polygon(ring)
        if not p.is_valid or p.area == 0:
            p = p.buffer(0)
        if p.is_empty or p.area == 0:
            continue
        outers.append(p)
    # Sort largest-first so holes attach to the smallest containing outer.
    outers.sort(key=lambda p: p.area, reverse=True)
    holes_for = {i: [] for i in range(len(outers))}
    assigned_outer = [True] * len(outers)
    # Second pass: rings that are holes will have been appended as outers;
    # re-classify any outer fully contained in a larger outer as a hole.
    # (Esri guarantees ring orientation, but containment is robust.)
    for i, cand in enumerate(outers):
        for j in range(i):
            if outers[j].contains(cand):
                holes_for[j].append(list(cand.exterior.coords))
                assigned_outer[i] = False
                break
    for i, outer in enumerate(outers):
        if not assigned_outer[i]:
            continue
        try:
            polys.append(Polygon(outer.exterior.coords, holes_for[i]))
        except Exception:
            polys.append(outer)
    return polys


def _esri_geometry_to_shapely(geom):
    """Convert one Esri JSON geometry dict to a shapely geometry (or None)."""
    if not geom:
        return None
    if "rings" in geom:
        polys = _esri_rings_to_polygons(geom["rings"])
        if not polys:
            return None
        if len(polys) == 1:
            return polys[0]
        from shapely.geometry import MultiPolygon
        return MultiPolygon(polys)
    if "x" in geom and "y" in geom:
        from shapely.geometry import Point
        return Point(geom["x"], geom["y"])
    return None


def _geojson_geom_to_shapely(geom):
    from shapely.geometry import shape
    try:
        return shape(geom)
    except Exception:
        return None


def _wkid_to_epsg(wkid):
    """Map common Esri WKIDs to EPSG codes (pyproj understands EPSG)."""
    mapping_wkid = {
        102100: 3857,  # Web Mercator
        3857: 3857,
        4326: 4326,
        4269: 4269,
        3566: 3566,
        102743: 3566,  # Esri code for NAD83(2011)/Utah ftUS -> EPSG 3566
        26912: 26912,  # NAD83 UTM 12N (metres)
    }
    return mapping_wkid.get(wkid, wkid)


def _detect_source_crs(doc):
    """Return an EPSG int for the source document.

    Esri FeatureSet: doc['spatialReference'] -> {'wkid': ...}.
    GeoJSON: assumed EPSG:4326 per RFC 7946.
    """
    if isinstance(doc, dict) and "spatialReference" in doc:
        sr = doc["spatialReference"] or {}
        wkid = sr.get("latestWkid") or sr.get("wkid") or 4326
        return _wkid_to_epsg(int(wkid))
    return 4326


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def _iter_source_features(doc):
    """Yield (attributes_dict, shapely_geometry_or_None) from a source doc."""
    if isinstance(doc, dict) and "features" in doc:
        feats = doc["features"]
        if feats and isinstance(feats[0], dict) and "attributes" in feats[0]:
            # Esri FeatureSet
            for f in feats:
                attrs = f.get("attributes") or {}
                yield attrs, _esri_geometry_to_shapely(f.get("geometry"))
            return
        # GeoJSON FeatureCollection
        for f in feats:
            props = (f.get("properties") or {}) if isinstance(f, dict) else {}
            geom = _geojson_geom_to_shapely(f.get("geometry")) if isinstance(f, dict) else None
            yield props, geom
        return
    raise ValueError("Unrecognized source format: expected Esri FeatureSet JSON "
                     "or GeoJSON FeatureCollection")


def load_parcels(source_path, district_field=None, limit=None, bbox=None):
    """Load parcels from a GIS source file -> list of W1-schema GeoJSON Features.

    Args:
        source_path: path to an Esri FeatureSet JSON (ArcGIS REST f=json) or
            a GeoJSON FeatureCollection of parcel polygons.
        district_field: name of the source attribute/property holding the
            zoning district code (e.g. "district", "ZONING"). If None, the
            emitted features carry no `district` unless the source already
            has a `district` property.
        limit: maximum number of features to return (None = all).
        bbox: optional (xmin, ymin, xmax, ymax) filter in the OUTPUT
            local-feet frame; a parcel is kept if its bounding box
            intersects the filter box.

    Returns:
        list of GeoJSON Feature dicts. Geometry is a Polygon in planar feet
        (EPSG:3566). Properties always include:
            parcel_id (str), crs ("local-feet"),
        and may include district, zone_label, plus real source attributes
        (address, city, county) when present.
    """
    if Transformer is None:  # pragma: no cover
        raise RuntimeError("pyproj is required for reprojection")
    with open(source_path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)

    src_epsg = _detect_source_crs(doc)
    to_feet = Transformer.from_crs(
        CRS.from_epsg(src_epsg), CRS.from_epsg(LOCAL_FEET_EPSG), always_xy=True
    ).transform

    out = []
    for idx, (attrs, geom) in enumerate(_iter_source_features(doc)):
        if geom is None or geom.is_empty:
            continue
        # Reproject to planar feet.
        try:
            g = shp_transform(to_feet, geom)
        except Exception:
            continue
        if g is None or g.is_empty:
            continue
        # Schema requires Polygon: keep the largest part of multi-part shapes,
        # and the exterior ring only (W1 schema: holes not handled downstream).
        if g.geom_type == "MultiPolygon":
            parts = sorted(g.geoms, key=lambda p: p.area, reverse=True)
            g = parts[0]
        if g.geom_type != "Polygon":
            continue
        if len(g.interiors) > 0:
            g = Polygon(g.exterior)  # documented: interior rings dropped
        if not g.is_valid:
            g = g.buffer(0)
            if g.is_empty or g.geom_type != "Polygon":
                continue
        if bbox is not None:
            xmin, ymin, xmax, ymax = bbox
            gx0, gy0, gx1, gy1 = g.bounds
            if gx1 < xmin or gx0 > xmax or gy1 < ymin or gy0 > ymax:
                continue

        parcel_id = attrs.get("PARCEL_ID") or attrs.get("parcel_id")
        if parcel_id is None:
            parcel_id = attrs.get("OBJECTID", idx)
        parcel_id = str(parcel_id)

        props = {"parcel_id": parcel_id, "crs": "local-feet"}
        if district_field and attrs.get(district_field):
            props["district"] = str(attrs[district_field])
        elif attrs.get("district"):
            props["district"] = str(attrs["district"])
        if attrs.get("zone_label"):
            props["zone_label"] = str(attrs["zone_label"])
        # Real, non-invented extras carried through verbatim from the source.
        for src_key, dst_key in (("PARCEL_ADD", "address"),
                                 ("parcel_add", "address"),
                                 ("PARCEL_CITY", "city"),
                                 ("parcel_city", "city"),
                                 ("County", "county"),
                                 ("county", "county")):
            if attrs.get(src_key) and dst_key not in props:
                props[dst_key] = str(attrs[src_key])
        props["source_srid"] = f"EPSG:{src_epsg}"

        out.append({
            "type": "Feature",
            "geometry": mapping(g),
            "properties": props,
        })
        if limit is not None and len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------------------
# Zoning join
# ---------------------------------------------------------------------------

def _load_zone_polygons(zoning_path):
    """Load (district, zone_label, shapely_polygon_in_4326) from a zoning source."""
    with open(zoning_path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    src_epsg = _detect_source_crs(doc)
    to_4326 = None
    if src_epsg != 4326:
        to_4326 = Transformer.from_crs(
            CRS.from_epsg(src_epsg), CRS.from_epsg(4326), always_xy=True
        ).transform
    zones = []
    for attrs, geom in _iter_source_features(doc):
        if geom is None or geom.is_empty:
            continue
        if to_4326 is not None:
            try:
                geom = shp_transform(to_4326, geom)
            except Exception:
                continue
        if geom.geom_type == "MultiPolygon":
            parts = list(geom.geoms)
        elif geom.geom_type == "Polygon":
            parts = [geom]
        else:
            continue
        district = attrs.get("ZONING") or attrs.get("district") or attrs.get("ZONE")
        label = attrs.get("ZONING_NAME") or attrs.get("zone_label") or ""
        for part in parts:
            if part.is_empty:
                continue
            zones.append((str(district) if district else None,
                          str(label) if label else None, part))
    return zones


def join_zoning(parcel_features, zoning_path):
    """Attach `district` / `zone_label` to parcel features via centroid join.

    For each parcel, the zoning polygon containing its centroid supplies the
    district. If no polygon contains the centroid (edge/gap cases), the
    nearest zone polygon is used and the property `district_provenance` is
    set to "nearest" instead of "centroid-contains" — never silent.
    Parcels whose centroid matches no zone at all keep no district.

    Mutates and returns parcel_features.
    """
    if Transformer is None:  # pragma: no cover
        raise RuntimeError("pyproj is required for the zoning join")
    zones = _load_zone_polygons(zoning_path)
    if not zones:
        raise ValueError(f"No zone polygons loaded from {zoning_path}")
    geoms = [z[2] for z in zones]
    tree = STRtree(geoms)

    to_4326 = Transformer.from_crs(
        CRS.from_epsg(LOCAL_FEET_EPSG), CRS.from_epsg(4326), always_xy=True
    ).transform

    for feat in parcel_features:
        props = feat["properties"]
        if props.get("district"):
            continue  # explicit district already present; do not override
        g_feet = _geojson_geom_to_shapely(feat["geometry"])
        if g_feet is None or g_feet.is_empty:
            continue
        centroid = shp_transform(to_4326, g_feet.centroid)

        district = label = None
        provenance = None
        for idx in tree.query(centroid, predicate="intersects"):
            d, l, _ = zones[idx]
            if d:
                district, label = d, l
                provenance = "centroid-contains"
                break
        if district is None:
            # Fallback: nearest zone polygon to the centroid.
            nearest = tree.nearest(centroid)
            if nearest is not None:
                d, l, _ = zones[int(nearest)]
                if d:
                    district, label = d, l
                    provenance = "nearest"
        if district is not None:
            props["district"] = district
            props["zone_label"] = label or ""
            props["district_provenance"] = provenance
    return parcel_features


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Sample real parcels from GIS and write W1-schema parcel files.")
    ap.add_argument("--source", required=True,
                    help="Parcel source: Esri FeatureSet JSON or GeoJSON")
    ap.add_argument("--zoning", default=None,
                    help="Zoning source for district join (Esri JSON / GeoJSON)")
    ap.add_argument("--sample", type=int, default=500,
                    help="Number of parcels to write (default 500)")
    ap.add_argument("--out", required=True, help="Output directory")
    ap.add_argument("--district-field", default=None,
                    help="Source attribute holding an existing district code")
    ap.add_argument("--bbox", nargs=4, type=float, default=None, metavar=("XMIN", "YMIN", "XMAX", "YMAX"),
                    help="Filter box in output planar-feet frame")
    args = ap.parse_args(argv)

    feats = load_parcels(args.source, district_field=args.district_field,
                         limit=args.sample, bbox=tuple(args.bbox) if args.bbox else None)
    if args.zoning:
        feats = join_zoning(feats, args.zoning)

    os.makedirs(args.out, exist_ok=True)
    written = 0
    for feat in feats:
        pid = feat["properties"]["parcel_id"]
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in pid)
        path = os.path.join(args.out, f"parcel_{safe}.geojson")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(feat, fh)
        written += 1

    index = {
        "type": "FeatureCollection",
        "crs_feet_frame": f"EPSG:{LOCAL_FEET_EPSG}",
        "count": written,
        "features": feats,
    }
    with open(os.path.join(args.out, "parcel_index.geojson"), "w", encoding="utf-8") as fh:
        json.dump(index, fh)
    with_district = sum(1 for f in feats if f["properties"].get("district"))
    print(f"Wrote {written} parcel files to {args.out} "
          f"({with_district} with district) + parcel_index.geojson")
    return 0


if __name__ == "__main__":
    sys.exit(main())