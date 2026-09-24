"""Deterministic geometry engine (shapely).

Build plan §5/§6: LLMs may propose operations, but this engine owns exact
coordinates and topology. There is intentionally no model call anywhere
in this module.

Strategy (scaffold v0, two subdivision classes):
  spine_road:
    1. Rotate the parcel into a local frame at the candidate road angle.
    2. Cut a road corridor (band) through the parcel at a fractional offset.
    3. Subdivide the developable area on each side of the road into lots by
       slicing vertical strips; each strip's frontage is measured along the
       road edge and its area is the strip clipped to the parcel.
    4. Filter strips against min area / min frontage; rotate back to the
       parcel frame.
  culdesac (narrow-parcel / bulb strategy — Tripp Lane GEOMETRY fix):
    1. A stem corridor runs from the parcel edge to a circular bulb
       (turnaround); the bulb radius defaults to the citable 50-ft
       turnaround ROW radius.
    2. Module bands tile along both sides of the stem, stopping short of
       the bulb.
    3. Wedge-shaped lots ring the bulb (frontage = bulb arc); the stem
       connection sector is excluded.
    4. Same area/frontage filters; rotate back to the parcel frame.

Product types:
  detached (default): min_frontage_ft is required; lot modules derive from
    it; the frontage filter gates every lot.
  attached_twinhome: min_frontage_ft is OPTIONAL (width-less frontage
    semantics — R-N-B §17.140.040 states area + setbacks but no minimum lot
    width, and ZONING_POLICY forbids inventing a width proxy). Lot modules
    are product unit widths (an explicit design search, not a zoning claim);
    the frontage filter is disabled, but frontage is still measured and
    reported per lot. Each strip is one twinhome unit (5,000 sqft); adjacent
    strips share the 0' common-wall boundary implicitly.

Varying (angle, road offset, lot module width) yields materially different
schemes: different lot counts, road lengths, and orientations.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from shapely.affinity import rotate
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
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


def _annular_sector(
    cx: float, cy: float, r_in: float, r_out: float,
    t1: float, t2: float, n: int = 32,
) -> Polygon:
    """Polygonal annular sector (wedge) spanning angles [t1, t2].

    r_in is deliberately allowed to be smaller than a bulb radius so the
    wedge overlaps the bulb disk; after the road is subtracted the lot's
    inner edge is exactly the bulb boundary (clean boolean, no slivers).
    """
    pts = []
    for k in range(n + 1):
        a = t1 + (t2 - t1) * k / n
        pts.append((cx + r_out * math.cos(a), cy + r_out * math.sin(a)))
    for k in range(n + 1):
        a = t2 - (t2 - t1) * k / n
        pts.append((cx + r_in * math.cos(a), cy + r_in * math.sin(a)))
    return Polygon(pts)


# Cul-de-sac turnaround ROW radius (ft). Murray Code §16.16.180 codifies the
# 50-ft turnaround radius; it is the citable default for the bulb strategy.
CULDESAC_BULB_RADIUS_FT = 50.0


def _build_culdesac_scheme_with_reason(
    parcel_poly: Polygon,
    zoning: Dict,
    *,
    scheme_id: str,
    parcel_id: str,
    angle_deg: float,
    stem_offset_frac: float,
    bulb_frac: float,
    bulb_radius_ft: float,
    lot_module_ft: float,
) -> Tuple[Optional[Scheme], str]:
    """Build one cul-de-sac scheme: a stem road terminating in a bulb.

    Strategy (addresses the Tripp Lane GEOMETRY miss — accuracy_taxonomy.md):
    narrow parcels where a through spine road wastes the wide end. A stem
    corridor runs from the parcel edge to a circular bulb; lots tile along
    the stem on both sides and wedge-shaped lots ring the bulb (their
    frontage is the bulb arc). Deterministic; same inputs → same scheme.

    Returns (scheme_or_None, reason_code) with the same reason vocabulary
    as _build_scheme_with_reason.
    """
    min_area = float(zoning["min_lot_area_sqft"])
    min_frontage = _min_frontage_or_none(zoning)  # None = width-less (attached)
    road_width = float(zoning["road_width_ft"])
    tol = 0.98  # allow 2% numerical slack on area/frontage

    centroid = parcel_poly.centroid
    local = rotate(parcel_poly, -angle_deg, origin=centroid, use_radians=False)
    minx, miny, maxx, maxy = local.bounds
    if maxx - minx < 2 * lot_module_ft or maxy - miny < road_width * 2:
        return None, REASON_PARCEL_TOO_SMALL  # parcel too small for this configuration

    stem_x = minx + stem_offset_frac * (maxx - minx)
    bulb_cy = miny + bulb_frac * (maxy - miny)
    bulb = Point(stem_x, bulb_cy).buffer(bulb_radius_ft, resolution=96)
    stem = box(stem_x - road_width / 2, miny - EXTEND,
               stem_x + road_width / 2, bulb_cy)
    road_poly = stem.union(bulb).intersection(local)
    road_poly = _largest_polygon(road_poly)
    if road_poly is None or road_poly.area < 1.0:
        return None, REASON_ROAD_MISSED

    develop = local.difference(road_poly)
    lots: List[Lot] = []
    lot_idx = 0

    def _add_lot(lot_poly: Polygon, frontage: float) -> Optional[Polygon]:
        """Validate, repair, and record one lot. Returns the final local
        polygon, or None if the lot was rejected."""
        nonlocal lot_idx
        if lot_poly.area < min_area * tol or not _frontage_ok(frontage, min_frontage, tol):
            return None
        # Guard against boolean-op slivers: repair validity before rotating.
        # buffer(0) collapses self-touches; the area change is negligible
        # (observed +0.2 sqft on an 8,478 sqft lot) and the area gate below
        # re-verifies the repaired polygon.
        if not lot_poly.is_valid:
            lot_poly = lot_poly.buffer(0)
            lot_poly = _largest_polygon(lot_poly)
            if lot_poly is None or lot_poly.area < min_area * tol:
                return None
        world = rotate(lot_poly, angle_deg, origin=centroid, use_radians=False)
        world_coords = [[round(px, 2), round(py, 2)] for px, py in world.exterior.coords]
        world_poly = Polygon(world_coords)
        if not world_poly.is_valid:
            # Rounding after rotation can re-break validity (collapsed
            # vertices); repair and re-extract. Area change is negligible.
            world_poly = world_poly.buffer(0)
            world_poly = _largest_polygon(world_poly)
            if world_poly is None:
                return None
            world_coords = [[round(px, 2), round(py, 2)] for px, py in world_poly.exterior.coords]
            world_poly = Polygon(world_coords)
            if not world_poly.is_valid:
                return None
        if world_poly.area < min_area * tol:
            return None
        # Clip to the parent: rotation+rounding can push a vertex a
        # hundredth of a foot outside (observed <=0.33 sqft). Clipping
        # keeps "lots contained in parent" exact, not approximate. The
        # clipped coords keep full precision (no re-rounding) so the clip
        # boundary is not re-broken by rounding.
        world_poly = world_poly.intersection(parcel_poly)
        world_poly = _largest_polygon(world_poly)
        if world_poly is None or world_poly.area < min_area * tol:
            return None
        world_coords = [[px, py] for px, py in world_poly.exterior.coords]
        lots.append(
            Lot(
                lot_id=f"{scheme_id}-L{lot_idx:02d}",
                polygon=world_coords,
                area_sqft=round(float(world_poly.area), 1),
                frontage_ft=round(float(frontage), 1),
            )
        )
        lot_idx += 1
        return lot_poly

    # --- stem lots: module bands along both sides of the stem, stopping
    # --- short of the bulb (the bulb's wedge lots own that ground).
    stem_top = bulb_cy - bulb_radius_ft
    stem_lots: List[Polygon] = []
    for side, x_lo, x_hi in (
        ("west", minx, stem_x - road_width / 2),
        ("east", stem_x + road_width / 2, maxx),
    ):
        edge_x = stem_x - road_width / 2 if side == "west" else stem_x + road_width / 2
        edge_line = LineString([(edge_x, miny - EXTEND), (edge_x, stem_top)])
        y = miny
        while y < stem_top - 1e-6:
            strip = box(x_lo, y, x_hi, y + lot_module_ft)
            lot_poly = _largest_polygon(develop.intersection(strip))
            y += lot_module_ft
            if lot_poly is None:
                continue
            placed = _add_lot(lot_poly, _frontage_along_road(lot_poly, edge_line))
            if placed is not None:
                stem_lots.append(placed)

    # Carve the placed stem lots out before the wedges so bulb lots can
    # never double-count ground (wedges dip below stem_top at their edges).
    if stem_lots:
        develop = develop.difference(unary_union(stem_lots))

    # --- bulb lots: wedge sectors ringing the bulb, excluding the sector
    # --- where the stem connects (straight down from the bulb center).
    half_excl = math.atan((road_width / 2) / bulb_radius_ft)
    start = -math.pi / 2 + half_excl
    end = 3 * math.pi / 2 - half_excl
    dtheta = lot_module_ft / bulb_radius_ft  # arc frontage ~= lot module
    bulb_circle = bulb.exterior
    t = start
    while t < end - 1e-9:
        t2 = min(t + dtheta, end)
        wedge = _annular_sector(
            stem_x, bulb_cy,
            bulb_radius_ft - 2.0, bulb_radius_ft + 300.0,
            t, t2,
        )
        lot_poly = _largest_polygon(develop.intersection(wedge))
        t = t2
        if lot_poly is None:
            continue
        inter = lot_poly.boundary.intersection(bulb_circle)
        frontage = 0.0 if inter.is_empty else float(inter.length)
        _add_lot(lot_poly, frontage)

    if not lots:
        return None, REASON_NO_CONFORMING_LOTS

    # Road centerlines: stem segment + bulb loop (closed). Length counts
    # both for infra costing; DXF iterates roads.
    stem_cl = LineString([(stem_x, miny), (stem_x, bulb_cy)])
    stem_cl = stem_cl.intersection(local)
    if stem_cl.is_empty:
        return None, REASON_NO_CENTERLINE
    if stem_cl.geom_type == "MultiLineString":
        stem_cl = max(stem_cl.geoms, key=lambda g: g.length)
    stem_world = rotate(stem_cl, angle_deg, origin=centroid, use_radians=False)
    bulb_world = rotate(bulb_circle, angle_deg, origin=centroid, use_radians=False)
    roads = [
        Road(
            road_id=f"{scheme_id}-R0",
            centerline=[[round(px, 2), round(py, 2)] for px, py in stem_world.coords],
            width_ft=road_width,
            length_ft=round(float(stem_cl.length), 1),
        ),
        Road(
            road_id=f"{scheme_id}-R1",
            centerline=[[round(px, 2), round(py, 2)] for px, py in bulb_world.coords],
            width_ft=road_width,
            length_ft=round(float(bulb_circle.length), 1),
        ),
    ]

    scheme = Scheme(
        scheme_id=scheme_id,
        parcel_id=parcel_id,
        lots=lots,
        roads=roads,
        params={
            "strategy": "culdesac",
            "angle_deg": angle_deg,
            "stem_offset_frac": stem_offset_frac,
            "bulb_frac": bulb_frac,
            "bulb_radius_ft": bulb_radius_ft,
            "lot_module_ft": lot_module_ft,
            "road_width_ft": road_width,
        },
    )
    scheme.fingerprint = fingerprint_geometry(scheme)
    return scheme, REASON_OK


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
    min_frontage = _min_frontage_or_none(zoning)  # None = width-less (attached)
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
            if lot_poly.area < min_area * tol or not _frontage_ok(frontage, min_frontage, tol):
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


ATTACHED_PRODUCT_TYPES = ("attached_twinhome", "attached_townhome")


def _is_attached(zoning: Dict) -> bool:
    """True for product types with width-less frontage semantics."""
    return zoning.get("product_type") in ATTACHED_PRODUCT_TYPES


def _lot_modules(zoning: Dict, *, for_culdesac: bool = False) -> List[float]:
    """Lot-width modules for the tiling grid.

    Detached spine-road: the historic 2-module grid (min_frontage,
    1.25x) — unchanged to preserve goldens.
    Detached cul-de-sac: 3-module grid (adds 1.125x; the Tripp 10-lot key).
    Attached twinhome: product unit widths (30/35/40) — an explicit design
      search (NOT a zoning claim; ZONING_POLICY forbids width proxies where
      the code states no minimum). Typical twinhome unit widths.
    Attached townhome: product unit widths (22/26/30) — narrower, as
      townhomes are typically 20-30 ft wide. Same width-less semantics.
    """
    pt = zoning.get("product_type")
    if pt == "attached_twinhome":
        return [30.0, 35.0, 40.0]
    if pt == "attached_townhome":
        return [22.0, 26.0, 30.0]
    min_frontage = float(zoning["min_frontage_ft"])
    if for_culdesac:
        return [min_frontage, round(min_frontage * 1.125, 1),
                round(min_frontage * 1.25, 1)]
    return [min_frontage, round(min_frontage * 1.25, 1)]


def _min_frontage_or_none(zoning: Dict) -> Optional[float]:
    """Width-less frontage semantics: returns None when the product type
    does not carry a frontage minimum (attached product with no
    min_frontage_ft). Callers must skip the frontage filter but still
    measure and report frontage."""
    v = zoning.get("min_frontage_ft")
    return float(v) if v is not None else None


def _frontage_ok(frontage: float, min_frontage: Optional[float], tol: float) -> bool:
    """Width-less frontage gate: when min_frontage is None (attached product
    with no code-stated width minimum), every measured frontage passes —
    frontage is reported, not gated."""
    if min_frontage is None:
        return True
    return frontage >= min_frontage * tol


def candidate_params(zoning: Dict) -> List[Dict]:
    """Seed parameter grid — the 'search' in constrained design-space search.

    Two strategies: the historic spine-road grid (unchanged, 24 configs) and
    the cul-de-sac grid (stem + bulb; addresses narrow-parcel under-yield).
    Every config carries a "strategy" key; the builder dispatches on it.
    Attached-twinhome zoning swaps the module basis to product unit widths.
    """
    grid = []
    for angle in (0.0, 30.0, 60.0, 90.0):
        for offset in (0.35, 0.5, 0.65):
            for module in _lot_modules(zoning):
                grid.append(
                    {"strategy": "spine_road", "angle_deg": angle,
                     "road_offset_frac": offset, "lot_module_ft": module}
                )
    for angle in (0.0, 90.0):
        for stem_offset in (0.35, 0.45, 0.55, 0.65):
            for bulb_frac in (0.7, 0.8, 0.9):
                for module in _lot_modules(zoning, for_culdesac=True):
                    grid.append(
                        {"strategy": "culdesac", "angle_deg": angle,
                         "stem_offset_frac": stem_offset, "bulb_frac": bulb_frac,
                         "bulb_radius_ft": CULDESAC_BULB_RADIUS_FT,
                         "lot_module_ft": module}
                    )
    return grid


def _signature(scheme: Scheme) -> Tuple[int, int, str]:
    return (
        len(scheme.lots),
        int(round(scheme.params["angle_deg"] / 30.0)),
        str(scheme.params.get("strategy", "spine_road")),
    )


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
        params = dict(p)
        strategy = params.pop("strategy", "spine_road")
        if strategy == "culdesac":
            s, reason = _build_culdesac_scheme_with_reason(
                parcel_poly, zoning, scheme_id=f"scheme_{i:02d}",
                parcel_id=parcel_id, **params
            )
        else:
            s, reason = _build_scheme_with_reason(
                parcel_poly, zoning, scheme_id=f"scheme_{i:02d}",
                parcel_id=parcel_id, **params
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
        "strategy": "spine_road+culdesac",
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
    # Lot-split family (DW-GEOM2): for small infill parcels where the
    # street-based strategies yield nothing, try splitting the parent into
    # N lots with no new streets. Each lot must meet min area and share
    # sufficient boundary with the parent exterior (access proxy).
    if not schemes:
        split_schemes = plan_generation_split(
            parcel_coords, zoning, parcel_id, max_schemes=max_schemes)
        if split_schemes:
            schemes = split_schemes
            diagnostic["lot_split_used"] = True
            diagnostic["lot_split_schemes_kept"] = len(schemes)
            diagnostic["verdict"] = "schemes_found"
    return schemes, diagnostic


def _mrr_axes(mrr: Polygon) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """Return (long_axis_unit, short_axis_unit) for an MRR."""
    coords = list(mrr.exterior.coords)[:4]
    # Find the longest edge -> long axis direction.
    best_len = -1.0
    best_vec = (1.0, 0.0)
    for i in range(4):
        x1, y1 = coords[i]
        x2, y2 = coords[(i + 1) % 4]
        dx, dy = x2 - x1, y2 - y1
        ln = (dx * dx + dy * dy) ** 0.5
        if ln > best_len:
            best_len = ln
            best_vec = (dx / ln, dy / ln) if ln > 0 else (1.0, 0.0)
    lx, ly = best_vec
    # Short axis is perpendicular.
    return (lx, ly), (-ly, lx)


def _split_polygon_by_axis(poly: Polygon, axis: Tuple[float, float],
                           n: int) -> List[Polygon]:
    """Split a polygon into n strips perpendicular to axis (equal MRR slices).

    Projects the MRR onto the axis, cuts at equal intervals, intersects each
    slab with the polygon. Returns the non-empty intersections.
    """
    from shapely.geometry import box
    mrr = poly.minimum_rotated_rectangle
    ax, ay = axis
    # Project MRR corners onto the axis.
    projs = [x * ax + y * ay for x, y in mrr.exterior.coords]
    lo, hi = min(projs), max(projs)
    # Perpendicular direction.
    px, py = -ay, ax
    # Project onto perpendicular for the slab extent.
    pprojs = [x * px + y * py for x, y in mrr.exterior.coords]
    plo, phi = min(pprojs), max(pprojs)
    # Add margin.
    margin = (phi - plo) * 0.1 + 1.0
    strips = []
    for i in range(n):
        a0 = lo + (hi - lo) * i / n
        a1 = lo + (hi - lo) * (i + 1) / n
        # Build a slab polygon: in (axis, perp) coordinates, then transform.
        # Slab corners in axis-perp space: (a0, plo-margin), (a1, plo-margin),
        # (a1, phi+margin), (a0, phi+margin).
        # Convert to xy: x = a*ax + p*px, y = a*ay + p*py.
        corners_ap = [(a0, plo - margin), (a1, plo - margin),
                      (a1, phi + margin), (a0, phi + margin)]
        corners_xy = [(a * ax + p * px, a * ay + p * py) for a, p in corners_ap]
        slab = Polygon(corners_xy)
        inter = poly.intersection(slab)
        # Keep only polygonal parts.
        if inter.is_empty:
            continue
        polys = []
        if inter.geom_type == "Polygon":
            polys = [inter]
        elif inter.geom_type == "MultiPolygon":
            polys = list(inter.geoms)
        elif inter.geom_type == "GeometryCollection":
            # Extract polygons (slab-boundary coincidences can yield lines).
            polys = [g for g in inter.geoms if g.geom_type == "Polygon"]
        # Keep the largest; small slivers are noise.
        polys = sorted([p for p in polys if p.area > 1.0],
                       key=lambda g: g.area, reverse=True)
        if polys:
            strips.append(polys[0])
    return strips


def plan_generation_split(
    parcel_coords: List[List[float]],
    zoning: Dict,
    parcel_id: str,
    max_schemes: int = 8,
) -> List[Scheme]:
    """Lot-split scheme family (DW-GEOM2): no-new-street infill splits.

    Partitions the parent into N lots (N=2..max) by slicing the MRR along
    its long or short axis. Each lot must be a valid polygon, meet
    min_lot_area, and share at least min_frontage_ft of boundary with the
    parent exterior (street-access proxy; the parent is assumed to have
    street frontage).

    Returns schemes ranked by lot count (desc), then by minimum lot area
    (desc, preferring balanced splits). No roads are generated (roads=[]).
    """
    from shapely.ops import unary_union
    poly = to_polygon(parcel_coords)
    if poly.is_empty or poly.area <= 0:
        return []
    min_area = float(zoning.get("min_lot_area_sqft", 0) or 0)
    if min_area <= 0:
        return []
    min_front = zoning.get("min_frontage_ft")
    min_front_f = float(min_front) if min_front else None

    max_n = int(poly.area // min_area)
    max_n = max(2, min(max_n, 8))  # infill scale; at least try 2
    if max_n < 2:
        return []

    parent_boundary = poly.boundary
    long_axis, short_axis = _mrr_axes(poly.minimum_rotated_rectangle)

    candidates = []
    for n in range(2, max_n + 1):
        for axis_name, axis in (("long", long_axis), ("short", short_axis)):
            strips = _split_polygon_by_axis(poly, axis, n)
            if len(strips) != n:
                continue
            # Validate.
            ok = True
            lots = []
            min_lot_area = float("inf")
            for i, s in enumerate(strips):
                if not s.is_valid:
                    s = s.buffer(0)
                if s.is_empty or s.area < min_area * 0.999:
                    ok = False
                    break
                # Access proxy: shared boundary with parent exterior.
                if min_front_f:
                    shared = s.boundary.intersection(parent_boundary).length
                    if shared < min_front_f * 0.999:
                        ok = False
                        break
                min_lot_area = min(min_lot_area, s.area)
                lots.append(Lot(
                    lot_id=f"{parcel_id}-split-{axis_name}-{n}-{i+1}",
                    polygon=[[round(float(x), 2), round(float(y), 2)]
                             for x, y in s.exterior.coords],
                    area_sqft=round(float(s.area), 1),
                    frontage_ft=round(float(
                        s.boundary.intersection(parent_boundary).length), 1)
                    if min_front_f else 0.0,
                    product_type="detached",
                ))
            if not ok:
                continue
            # No overlap (strips from a partition shouldn't overlap, but check).
            union_area = unary_union(strips).area
            if abs(union_area - sum(s.area for s in strips)) > 1.0:
                continue
            scheme_id = f"{parcel_id}-split-{axis_name}-{n}"
            candidates.append(((-n, -min_lot_area), Scheme(
                scheme_id=scheme_id,
                parcel_id=parcel_id,
                lots=lots,
                roads=[],
                fingerprint="",
            )))

    candidates.sort(key=lambda t: t[0])
    schemes = [s for _, s in candidates[:max_schemes]]
    # Assign deterministic fingerprints.
    from .schema import fingerprint_geometry
    for s in schemes:
        s.fingerprint = fingerprint_geometry(s)
    return schemes


def _partition_parcel(parcel_poly: Polygon, fractions: List[float]) -> List[Polygon]:
    """Split a parcel into sub-parcels by area fraction.

    Uses the minimum rotated rectangle to find the long axis, then cuts
    perpendicular to it at cumulative-fraction positions. Deterministic.
    For rectangles the sub-parcel areas match the fractions exactly; for
    irregular parcels they are approximate (the caller allocates by the
    approved program, not by exact geometry).
    """
    assert abs(sum(fractions) - 1.0) < 1e-6, f"fractions sum to {sum(fractions)}"
    mrr = parcel_poly.minimum_rotated_rectangle
    # Long axis: the MRR's longer edge direction.
    coords = list(mrr.exterior.coords)
    # Find the longest edge.
    best = None
    for i in range(4):
        x1, y1 = coords[i]
        x2, y2 = coords[(i + 1) % 4]
        length = math.hypot(x2 - x1, y2 - y1)
        if best is None or length > best[0]:
            best = (length, math.atan2(y2 - y1, x2 - x1))
    angle = best[1]
    # Rotate so the long axis is horizontal; split the x-range.
    centroid = parcel_poly.centroid
    local = rotate(parcel_poly, -angle, origin=centroid, use_radians=True)
    minx, _, maxx, _ = local.bounds
    width = maxx - minx
    sub_parcels = []
    x0 = minx
    for i, frac in enumerate(fractions):
        x1 = minx + width * sum(fractions[: i + 1])
        strip = box(x0, local.bounds[1] - 1, x1, local.bounds[3] + 1)
        sub = local.intersection(strip)
        # Rotate back to the parcel frame.
        sub_world = rotate(sub, angle, origin=centroid, use_radians=True)
        # Keep only polygonal parts.
        if sub_world.is_empty:
            sub_parcels.append(Polygon())
        elif isinstance(sub_world, Polygon):
            sub_parcels.append(sub_world)
        else:  # MultiPolygon — take the largest piece.
            sub_parcels.append(_largest_polygon(sub_world))
        x0 = x1
    return sub_parcels


def plan_generation_mixed(
    parcel_coords: List[List[float]],
    product_specs: List[Dict],
    parcel_id: str,
    max_schemes: int = 5,
) -> Tuple[List[Scheme], Dict]:
    """Mixed-product scheme generation (DW-MIX1).

    product_specs: list of dicts, each with:
      - product_type: "detached" | "attached_twinhome" | "attached_townhome"
      - zoning: dict (must include product_type; dimensional inputs per type)
      - approved_units: int (approved count for this product; used for
        area allocation and per-product scoring)
      - area_fraction: float, optional (if absent, derived from
        approved_units * min_lot_area, i.e., land allocated proportional
        to the approved program)

    The parcel is partitioned by area fraction; each sub-parcel runs the
    single-product plan_generation with its product's zoning; the top
    scheme per product is combined into mixed schemes with lots tagged
    by product_type. Per-product counts are reported for scoring.

    Returns (mixed_schemes, diagnostic). This is a proof-of-concept for
    the Daybreak 11B Plat 2 class (59 detached + 32 townhomes); the plat
    itself is unscored (no parent polygon, no P-C dims sourced).
    """
    from .schema import Scheme as SchemeModel

    parcel_poly = to_polygon(parcel_coords)
    # Derive area fractions from the approved program if not given.
    total_program = 0.0
    for spec in product_specs:
        if "area_fraction" not in spec:
            min_a = float(spec["zoning"]["min_lot_area_sqft"])
            total_program += spec["approved_units"] * min_a
    fractions = []
    for spec in product_specs:
        if "area_fraction" in spec:
            fractions.append(float(spec["area_fraction"]))
        else:
            min_a = float(spec["zoning"]["min_lot_area_sqft"])
            fractions.append(spec["approved_units"] * min_a / total_program)
    # Normalize (in case explicit fractions don't sum to 1).
    s = sum(fractions)
    fractions = [f / s for f in fractions]

    sub_parcels = _partition_parcel(parcel_poly, fractions)
    diagnostic: Dict = {
        "strategy": "mixed_product",
        "products": [],
        "area_fractions": [round(f, 4) for f in fractions],
    }
    # Generate per product on its sub-parcel.
    product_schemes = []
    for spec, sub_poly in zip(product_specs, sub_parcels):
        pt = spec["product_type"]
        zoning = dict(spec["zoning"])
        zoning["product_type"] = pt
        sub_coords = [list(c) for c in sub_poly.exterior.coords] if not sub_poly.is_empty else []
        if not sub_coords:
            schemes, diag = [], {"verdict": "no_schemes__empty_subparcel"}
        else:
            schemes, diag = plan_generation(
                sub_coords, zoning, f"{parcel_id}-{pt}", max_schemes=max_schemes
            )
        # Tag lots with the product type.
        for sch in schemes:
            for lot in sch.lots:
                lot.product_type = pt
        product_schemes.append(schemes)
        diagnostic["products"].append({
            "product_type": pt,
            "approved_units": spec["approved_units"],
            "sub_parcel_area_sqft": round(float(sub_poly.area), 1) if not sub_poly.is_empty else 0.0,
            "schemes_found": len(schemes),
            "top_lots": len(schemes[0].lots) if schemes else 0,
        })
    # Combine the top scheme per product into mixed schemes.
    # For the PoC, take the top-1 per product; the mixed scheme's lots are
    # the union, tagged by product_type.
    mixed = []
    # Use the top scheme from each product (index 0). If any product has
    # no schemes, the mixed result is empty for that combination.
    tops = [ps[0] if ps else None for ps in product_schemes]
    if all(t is not None for t in tops):
        all_lots = []
        all_roads = []
        for sch in tops:
            all_lots.extend(sch.lots)
            all_roads.extend(sch.roads)
        mixed_scheme = SchemeModel(
            scheme_id=f"{parcel_id}-mixed-00",
            parcel_id=parcel_id,
            lots=all_lots,
            roads=all_roads,
            params={
                "strategy": "mixed_product",
                "products": [s["product_type"] for s in product_specs],
                "area_fractions": [round(f, 4) for f in fractions],
            },
            provenance=[{"step": "plan_generation_mixed", "inputs": "synthetic"}],
        )
        mixed_scheme.fingerprint = fingerprint_geometry(mixed_scheme)
        mixed.append(mixed_scheme)
    diagnostic["mixed_schemes"] = len(mixed)
    if mixed:
        counts: Dict[str, int] = {}
        for lot in mixed[0].lots:
            counts[lot.product_type] = counts.get(lot.product_type, 0) + 1
        diagnostic["per_product_counts"] = counts
    return mixed, diagnostic
