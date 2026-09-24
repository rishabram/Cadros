"""Validation engine — deterministic rule checks (build plan §7, §14).

Every check is a pure function of geometry + RuleBindings. The agent must
never silently infer a rule: each result cites its rule_id and source.
"""
from __future__ import annotations

from typing import Dict, List

from shapely.geometry import LineString, Polygon

from .schema import CheckResult, RuleBinding, Scheme


def default_rules(zoning: Dict, parcel_area_sqft: float) -> List[RuleBinding]:
    src = zoning.get("source", "inputs/zoning.json")
    return [
        RuleBinding(
            rule_id="R-1",
            description="Minimum lot area",
            operator=">=",
            value=float(zoning["min_lot_area_sqft"]),
            unit="sqft",
            source=src,
        ),
        RuleBinding(
            rule_id="R-2",
            description="Minimum lot frontage along road",
            operator=">=",
            value=float(zoning["min_frontage_ft"]),
            unit="ft",
            source=src,
        ),
        RuleBinding(
            rule_id="R-3",
            description="Lots contained within parcel boundary",
            operator="within",
            value=0.0,
            unit="",
            source="topology check (build plan §7)",
        ),
        RuleBinding(
            rule_id="R-4",
            description="No overlapping lots",
            operator="==",
            value=0.0,
            unit="sqft overlap",
            source="topology check (build plan §7)",
        ),
        RuleBinding(
            rule_id="R-5",
            description="Road connects to parcel boundary",
            operator="touches",
            value=2.0,
            unit="boundary connections",
            source="topology check (build plan §7)",
        ),
        RuleBinding(
            rule_id="R-6",
            description="Yield sanity: lots <= parcel_area / min_lot_area",
            operator="<=",
            value=parcel_area_sqft / float(zoning["min_lot_area_sqft"]),
            unit="lots",
            source="derived from R-1",
        ),
    ]


def validate_scheme(
    scheme: Scheme, parcel_coords: List[List[float]], zoning: Dict
) -> List[CheckResult]:
    parcel = Polygon(parcel_coords)
    if not parcel.is_valid:
        parcel = parcel.buffer(0)
    lot_polys = [Polygon(l.polygon) for l in scheme.lots]
    results: List[CheckResult] = []
    min_area = float(zoning["min_lot_area_sqft"])
    min_frontage = float(zoning["min_frontage_ft"])

    # R-1: min lot area
    bad = [l.lot_id for l in scheme.lots if l.area_sqft < min_area * 0.98]
    results.append(
        CheckResult(
            rule_id="R-1",
            status="fail" if bad else "pass",
            detail=f"{len(scheme.lots) - len(bad)}/{len(scheme.lots)} lots meet min area"
            + (f"; failing: {', '.join(bad[:5])}" if bad else ""),
        )
    )

    # R-2: min frontage
    bad = [l.lot_id for l in scheme.lots if l.frontage_ft < min_frontage * 0.98]
    results.append(
        CheckResult(
            rule_id="R-2",
            status="fail" if bad else "pass",
            detail=f"{len(scheme.lots) - len(bad)}/{len(scheme.lots)} lots meet min frontage"
            + (f"; failing: {', '.join(bad[:5])}" if bad else ""),
        )
    )

    # R-3: containment (small tolerance for float noise)
    outside = [
        l.lot_id
        for l, p in zip(scheme.lots, lot_polys)
        if not p.within(parcel.buffer(0.5))
    ]
    results.append(
        CheckResult(
            rule_id="R-3",
            status="fail" if outside else "pass",
            detail="all lots within parcel"
            if not outside
            else f"lots outside parcel: {', '.join(outside[:5])}",
        )
    )

    # R-4: overlap
    max_overlap = 0.0
    for i in range(len(lot_polys)):
        for j in range(i + 1, len(lot_polys)):
            max_overlap = max(max_overlap, lot_polys[i].intersection(lot_polys[j]).area)
    results.append(
        CheckResult(
            rule_id="R-4",
            status="fail" if max_overlap > 1.0 else "pass",
            detail=f"max pairwise lot overlap: {max_overlap:.2f} sqft",
        )
    )

    # R-5: road connectivity — road band must touch the parcel boundary
    # twice (through-road) or once (stub: warning, needs turnaround review).
    touches = 0
    if scheme.roads:
        r = scheme.roads[0]
        band = LineString(r.centerline).buffer(r.width_ft / 2, cap_style=2)
        inter = band.intersection(parcel.boundary)
        if not inter.is_empty:
            touches = (
                len(inter.geoms)
                if inter.geom_type in ("MultiLineString", "GeometryCollection")
                else 1
            )
    results.append(
        CheckResult(
            rule_id="R-5",
            status="pass" if touches >= 2 else ("warning" if touches == 1 else "fail"),
            detail=(
                f"road meets parcel boundary in {touches} place(s)"
                + (" — stub end: verify turnaround/cul-de-sac standard" if touches == 1 else "")
            ),
        )
    )

    # R-6: yield sanity
    cap = parcel.area / min_area
    results.append(
        CheckResult(
            rule_id="R-6",
            status="fail" if len(scheme.lots) > cap else "pass",
            detail=f"{len(scheme.lots)} lots vs theoretical max {cap:.1f}",
        )
    )
    return results


def scheme_is_clean(results: List[CheckResult]) -> bool:
    return all(r.status == "pass" for r in results)
