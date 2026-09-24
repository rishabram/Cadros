"""Deterministic geometry engine (shapely).

Build plan §5/§6: LLMs may propose operations, but this engine owns exact
coordinates and topology. There is intentionally no model call anywhere
in this module.

Strategy (scaffold v0, single spine-road subdivision class):
  1. Rotate the parcel into a local frame at the candidate road angle.
  2. Cut a road corridor (band) through the parcel at a fractional offset.
  3. Subdivide the developable area on each side of the road into lots by
     slicing vertical strips; each strip's frontage is measured along the
     road edge and its area is the strip clipped to the parcel.
  4. Filter strips against min area / min frontage; rotate back to the
     parcel frame.

Varying (angle, road offset, lot module width) yields materially different
schemes: different lot counts, road lengths, and orientations.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from shapely.affinity import rotate
from shapely.geometry import LineString, MultiPolygon, Polygon, box
from shapely.ops import unary_union

from .schema import Lot, Road, Scheme, fingerprint_geometry

EXTEND = 100.0  # how far past the parcel bbox the road band reaches (ft)

# Diagnostic reason codes: why a candidate (angle, offset, module)
# configuration produced no scheme. Recorded by plan_generation() so a
# no-schemes result is never silent.
REASON_OK = "ok"
REASON_PARCEL_TOO_SMALL = "parcel_too_small_for_config"
REASON_ROAD_MISSED = "road_band_missed_parcel"
REASON_NO_CONFORMING_LOTS = "no_conforming_lots"
REASON_NO_CENTERLINE = "road_centerline_empty"
REASON_BELOW_MIN_LOTS = "below_min_lots_threshold"

# A parcel whose area fits fewer than this many min-lot-areas is not expected
# to subdivide; no-schemes there is routine, not a diagnostic event.
SIZE_THRESHOLD_RATIO = 2.0


def to_polygon(coords: List[List[float]]) -> Polygon:
    poly = Polygon(coords)
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty or poly.area == 0:
        raise ValueError(
            "parcel boundary is empty or has zero area — "
            "cannot generate subdivision schemes"
        )
    return poly


def _largest_polygon(geom) -> Optional[Polygon]:
    if geom.is_empty:
        return None
    if isinstance(geom, Polygon):
        return geom
    if isinstance(geom, MultiPolygon):
        parts = [g for g in geom.geoms if isinstance(g, Polygon) and g.area > 0]
        return max(parts, key=lambda g: g.area) if parts else None
    return None


def _frontage_along_road(lot_poly: Polygon, edge_line: LineString) -> float:
    """Lot frontage = length of lot boundary coincident with the road edge."""
    inter = lot_poly.boundary.intersection(edge_line)
    if inter.is_empty:
        return 0.0
    return float(inter.length)


def build_scheme(
    parcel_poly: Polygon,
    zoning: Dict,
    *,
    scheme_id: str,
    parcel_id: str,
    angle_deg: float,
    road_offset_frac: float,
    lot_module_ft: float,
) -> Optional[Scheme]:
    """Build one scheme; None when the configuration is infeasible.

    Thin wrapper over _build_scheme_with_reason — behavior is identical,
    the diagnostic reason is discarded.
    """
    scheme, _reason = _build_scheme_with_reason(
        parcel_poly,
        zoning,
        scheme_id=scheme_id,
        parcel_id=parcel_id,
        angle_deg=angle_deg,
        road_offset_frac=road_offset_frac,
        lot_module_ft=lot_module_ft,
    )
    return scheme


def _build_scheme_with_reason(
    parcel_poly: Polygon,
    zoning: Dict,
    *,
    scheme_id: str,
    parcel_id: str,
    angle_deg: float,
    road_offset_frac: float,
    lot_module_ft: float,
) -> Tuple[Optional[Scheme], str]:
    """Build one scheme, returning (scheme_or_None, reason_code).

    The geometry is exactly what build_scheme() computes; the reason code
    names which feasibility gate rejected the configuration so callers can
    diagnose silent no-schemes results.
    """
    min_area = float(zoning["min_lot_area_sqft"])
    min_frontage = float(zoning["min_frontage_ft"])
    road_width = float(zoning["road_width_ft"])
    tol = 0.98  # allow 2% numerical slack on area/frontage

    centroid = parcel_poly.centroid
    local = rotate(parcel_poly, -angle_deg, origin=centroid, use_radians=False)
    minx, miny, maxx, maxy = local.bounds
    if maxx - minx < 2 * lot_module_ft or maxy - miny < road_width * 2:
        return None, REASON_PARCEL_TOO_SMALL  # parcel too small for this configuration

    y0 = miny + road_offset_frac * (maxy - miny)
    road_band = box(minx - EXTEND, y0 - road_width / 2, maxx + EXTEND, y0 + road_width / 2)
    road_poly = road_band.intersection(local)
    road_poly = _largest_polygon(road_poly)
    if road_poly is None or road_poly.area < 1.0:
        return None, REASON_ROAD_MISSED

    develop = local.difference(road_poly)
    lots: List[Lot] = []
    lot_idx = 0

    for side, y_edge in (("north", y0 + road_width / 2), ("south", y0 - road_width / 2)):
        half_box = (
            box(minx - EXTEND, y_edge, maxx + EXTEND, maxy + EXTEND)
            if side == "north"
            else box(minx - EXTEND, miny - EXTEND, maxx + EXTEND, y_edge)
        )
        half = develop.intersection(half_box)
        if half.is_empty:
            continue
        edge_line = LineString([(minx - EXTEND, y_edge), (maxx + EXTEND, y_edge)])

        x = minx
        while x < maxx - 1e-6:
            strip = box(x, miny - EXTEND, x + lot_module_ft, maxy + EXTEND)
            raw = half.intersection(strip)
            lot_poly = _largest_polygon(raw)
            x += lot_module_ft
            if lot_poly is None:
                continue
            frontage = _frontage_along_road(lot_poly, edge_line)
            if lot_poly.area < min_area * tol or frontage < min_frontage * tol:
                continue
            # rotate back to parcel frame
            world = rotate(lot_poly, angle_deg, origin=centroid, use_radians=False)
            lots.append(
                Lot(
                    lot_id=f"{scheme_id}-L{lot_idx:02d}",
                    polygon=[[round(px, 2), round(py, 2)] for px, py in world.exterior.coords],
                    area_sqft=round(float(lot_poly.area), 1),
                    frontage_ft=round(float(frontage), 1),
                )
            )
            lot_idx += 1

    if not lots:
        return None, REASON_NO_CONFORMING_LOTS

    # Road centerline clipped to parcel (for length + DXF + connectivity check)
    cl_raw = LineString([(minx - EXTEND, y0), (maxx + EXTEND, y0)]).intersection(local)
    if cl_raw.is_empty:
        return None, REASON_NO_CENTERLINE
    if cl_raw.geom_type == "MultiLineString":
        cl = max(cl_raw.geoms, key=lambda g: g.length)
    else:
        cl = cl_raw
    cl_world = rotate(cl, angle_deg, origin=centroid, use_radians=False)
    road = Road(
        road_id=f"{scheme_id}-R0",
        centerline=[[round(px, 2), round(py, 2)] for px, py in cl_world.coords],
        width_ft=road_width,
        length_ft=round(float(cl.length), 1),
    )

    scheme = Scheme(
        scheme_id=scheme_id,
        parcel_id=parcel_id,
        lots=lots,
        roads=[road],
        params={
            "angle_deg": angle_deg,
            "road_offset_frac": road_offset_frac,
            "lot_module_ft": lot_module_ft,
            "road_width_ft": road_width,
        },
    )
    scheme.fingerprint = fingerprint_geometry(scheme)
    return scheme, REASON_OK


def candidate_params(zoning: Dict) -> List[Dict]:
    """Seed parameter grid — the 'search' in constrained design-space search."""
    min_frontage = float(zoning["min_frontage_ft"])
    grid = []
    for angle in (0.0, 30.0, 60.0, 90.0):
        for offset in (0.35, 0.5, 0.65):
            for module in (min_frontage, round(min_frontage * 1.25, 1)):
                grid.append(
                    {"angle_deg": angle, "road_offset_frac": offset, "lot_module_ft": module}
                )
    return grid


def _signature(scheme: Scheme) -> Tuple[int, int]:
    return (len(scheme.lots), int(round(scheme.params["angle_deg"] / 30.0)))


def _generate_with_reasons(
    parcel_poly: Polygon,
    zoning: Dict,
    parcel_id: str,
    max_schemes: int,
    min_schemes: int,
    min_lots: int,
) -> Tuple[List[Scheme], "Counter[str]"]:
    """Inner generation pass: build candidates, tally per-candidate outcomes.

    Returns (picked_schemes, reason_counts). The scheme construction,
    ranking, diversity selection, and renumbering are exactly the historic
    generate_schemes() logic; only the lot-count acceptance threshold is
    parameterized (historic value: 4).
    """
    from collections import Counter

    reasons: Counter = Counter()
    built: List[Scheme] = []
    for i, p in enumerate(candidate_params(zoning)):
        s, reason = _build_scheme_with_reason(
            parcel_poly, zoning, scheme_id=f"scheme_{i:02d}", parcel_id=parcel_id, **p
        )
        if s is None:
            reasons[reason] += 1
            continue
        if len(s.lots) < min_lots:
            reasons[REASON_BELOW_MIN_LOTS] += 1
            continue
        reasons[REASON_OK] += 1
        built.append(s)

    # rank: most lots first, then shorter road (cheaper) as tiebreak
    built.sort(key=lambda s: (-len(s.lots), sum(r.length_ft for r in s.roads)))

    picked: List[Scheme] = []
    seen = set()
    for s in built:
        sig = _signature(s)
        if sig not in seen:
            picked.append(s)
            seen.add(sig)
        if len(picked) >= max_schemes:
            break
    if len(picked) < min_schemes:
        # relax diversity: fill with best remaining regardless of signature
        for s in built:
            if s not in picked:
                picked.append(s)
            if len(picked) >= min_schemes:
                break
    # renumber for stable ids
    for j, s in enumerate(picked):
        old = s.scheme_id
        s.scheme_id = f"scheme_{j:02d}"
        for k, lot in enumerate(s.lots):
            lot.lot_id = f"scheme_{j:02d}-L{k:02d}"
        for r in s.roads:
            r.road_id = f"scheme_{j:02d}-R0"
        s.fingerprint = fingerprint_geometry(s)
    return picked, reasons


def generate_schemes(
    parcel_coords: List[List[float]],
    zoning: Dict,
    parcel_id: str,
    max_schemes: int = 10,
    min_schemes: int = 5,
    min_lots: int = 4,
) -> List[Scheme]:
    """Generate candidate schemes and keep a materially different subset.

    Diversity rule: prefer distinct (lot count, road angle) signatures so the
    returned set spans the design space instead of cosmetic variants.
    Deterministic — same inputs always yield the same schemes.

    min_lots (default 4) is the per-scheme acceptance threshold: candidates
    yielding fewer lots are discarded. The default preserves the historic
    behavior exactly; pass a smaller value (or use plan_generation()) to
    admit small subdivisions.
    """
    parcel_poly = to_polygon(parcel_coords)
    schemes, _reasons = _generate_with_reasons(
        parcel_poly, zoning, parcel_id, max_schemes, min_schemes, min_lots
    )
    return schemes


def plan_generation(
    parcel_coords: List[List[float]],
    zoning: Dict,
    parcel_id: str,
    max_schemes: int = 10,
    min_schemes: int = 5,
    min_lots_primary: int = 4,
    min_lots_fallback: int = 2,
) -> Tuple[List[Scheme], Dict]:
    """Two-pass scheme generation with a machine-readable diagnostic.

    Primary pass uses min_lots_primary (default 4, the historic threshold).
    The fallback pass (min_lots_fallback, default 2) runs ONLY when the
    primary pass yields nothing AND the parcel is large enough to plausibly
    subdivide (area >= SIZE_THRESHOLD_RATIO * min_lot_area). Parcels that
    produced schemes in the primary pass are therefore byte-identical to
    the historic generate_schemes() output.

    Returns (schemes, diagnostic). The diagnostic always names the blocking
    reasons per pass so a no-schemes result is never silent; its "verdict"
    is one of:
      - "schemes_found"
      - "no_schemes__below_size_threshold" (parcel too small to subdivide;
        the expected result, not a defect)
      - "no_schemes__unexpected" (parcel looked subdividable but no
        conforming scheme exists under the spine-road strategy — loud)
    """
    parcel_poly = to_polygon(parcel_coords)
    parcel_area = float(parcel_poly.area)
    min_area = float(zoning["min_lot_area_sqft"])
    area_ratio = parcel_area / min_area if min_area > 0 else 0.0

    schemes, reasons = _generate_with_reasons(
        parcel_poly, zoning, parcel_id, max_schemes, min_schemes, min_lots_primary
    )
    diagnostic: Dict = {
        "strategy": "spine_road",
        "candidates_evaluated": len(candidate_params(zoning)),
        "size_threshold_ratio": SIZE_THRESHOLD_RATIO,
        "area_min_lot_ratio": round(area_ratio, 2),
        "primary_min_lots": min_lots_primary,
        "primary_schemes_kept": len(schemes),
        "primary_blocking_reasons": dict(sorted(reasons.items())),
        "fallback_used": False,
    }
    if not schemes and area_ratio >= SIZE_THRESHOLD_RATIO:
        schemes, fb_reasons = _generate_with_reasons(
            parcel_poly, zoning, parcel_id, max_schemes, min_schemes, min_lots_fallback
        )
        diagnostic["fallback_used"] = True
        diagnostic["fallback_min_lots"] = min_lots_fallback
        diagnostic["fallback_schemes_kept"] = len(schemes)
        diagnostic["fallback_blocking_reasons"] = dict(sorted(fb_reasons.items()))
    elif not schemes:
        diagnostic["fallback_skipped_reason"] = (
            f"parcel area fits {area_ratio:.1f}x min_lot_area "
            f"(< {SIZE_THRESHOLD_RATIO}x size threshold); "
            "no-schemes is the expected result"
        )

    blocking = dict(diagnostic["primary_blocking_reasons"])
    if diagnostic["fallback_used"]:
        blocking = dict(diagnostic["fallback_blocking_reasons"])
    non_ok = {k: v for k, v in blocking.items() if k != REASON_OK}
    diagnostic["top_blocking_reason"] = (
        max(non_ok, key=lambda k: non_ok[k]) if non_ok else REASON_OK
    )
    if schemes:
        diagnostic["verdict"] = "schemes_found"
    elif area_ratio < SIZE_THRESHOLD_RATIO:
        diagnostic["verdict"] = "no_schemes__below_size_threshold"
    else:
        diagnostic["verdict"] = "no_schemes__unexpected"
    return schemes, diagnostic
